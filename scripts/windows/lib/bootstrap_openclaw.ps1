Set-StrictMode -Version Latest

function Test-OpenClawPreferred {
    param([Parameter(Mandatory)][string]$NpmPrefix)

    $PackageRoot = Join-Path $NpmPrefix 'node_modules\openclaw'
    $PackageJson = Join-Path $PackageRoot 'package.json'
    $EntryPoint = Join-Path $PackageRoot 'openclaw.mjs'
    $Command = Join-Path $NpmPrefix 'openclaw.cmd'
    $Marker = Join-Path $NpmPrefix '.openclaw-local-install.json'
    foreach ($RequiredPath in @($PackageJson, $EntryPoint, $Command, $Marker)) {
        if (-not (Test-Path -LiteralPath $RequiredPath)) {
            return $false
        }
    }

    try {
        $Installed = [string](Get-Content -Raw -LiteralPath $PackageJson | ConvertFrom-Json).version
        $MarkerData = Get-Content -Raw -LiteralPath $Marker | ConvertFrom-Json
    }
    catch {
        return $false
    }

    return (
        $Installed -eq [string]$Lock.openclaw.preferred -and
        [string]$MarkerData.openclaw_version -eq [string]$Lock.openclaw.preferred -and
        [string]$MarkerData.node_version -eq [string]$Lock.node.preferred -and
        [string]$MarkerData.integrity -eq [string]$Lock.openclaw.integrity
    )
}

function Install-OpenClawPreferred {
    param([Parameter(Mandatory)][string]$RuntimeHome)

    $NodeHome = Join-Path $RuntimeHome 'node'
    $NpmPrefix = Join-Path $RuntimeHome 'npm-global'
    if (Test-OpenClawPreferred -NpmPrefix $NpmPrefix) {
        Write-Host "OK  OpenClaw $($Lock.openclaw.preferred) déjà présent."
        return
    }

    $Node = Join-Path $NodeHome 'node.exe'
    if (-not (Test-Path -LiteralPath $Node)) {
        Write-BootstrapFailure "Runtime Node.js introuvable avant installation OpenClaw: $Node"
    }

    $PathParts = @(
        $env:PATH -split ';' |
            Where-Object { $_ -and $_ -ne $NodeHome }
    )
    $env:PATH = (@($NodeHome) + $PathParts) -join ';'

    $ResolvedNode = Get-Command node.exe -ErrorAction SilentlyContinue
    if (-not $ResolvedNode -or $ResolvedNode.Source -ne $Node) {
        Write-BootstrapFailure "Le runtime Node.js local n'est pas prioritaire dans le PATH du processus: $Node"
    }

    $DetectedVersion = (& node.exe --version 2>$null).Trim()
    if ($DetectedVersion -ne "v$($Lock.node.preferred)") {
        Write-BootstrapFailure "Node.js $DetectedVersion détecté pour OpenClaw, attendu: v$($Lock.node.preferred)."
    }

    $Npm = Join-Path $NodeHome 'npm.cmd'
    if (-not (Test-Path -LiteralPath $Npm)) {
        Write-BootstrapFailure "npm.cmd introuvable dans le runtime Node.js local: $Npm"
    }

    $Temp = Join-Path ([IO.Path]::GetTempPath()) ("openclaw-local-npm-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $Temp -Force | Out-Null
    try {
        $PackOutput = & $Npm pack "openclaw@$($Lock.openclaw.preferred)" `
            --ignore-scripts --pack-destination $Temp --json
        if ($LASTEXITCODE -ne 0) {
            Write-BootstrapFailure 'npm pack OpenClaw a échoué.'
        }
        $PackInfo = @(($PackOutput -join [Environment]::NewLine) | ConvertFrom-Json)
        if ($PackInfo.Count -ne 1 -or -not $PackInfo[0].filename) {
            Write-BootstrapFailure 'Réponse npm pack invalide.'
        }
        $Tarball = Join-Path $Temp ([string]$PackInfo[0].filename)
        $Stream = [IO.File]::OpenRead($Tarball)
        $Hasher = [Security.Cryptography.SHA512]::Create()
        try {
            $Digest = $Hasher.ComputeHash($Stream)
        }
        finally {
            $Hasher.Dispose()
            $Stream.Dispose()
        }
        $ActualIntegrity = 'sha512-' + [Convert]::ToBase64String($Digest)
        if ($ActualIntegrity -ne [string]$Lock.openclaw.integrity) {
            Write-BootstrapFailure 'Tarball OpenClaw rejeté: intégrité SRI différente du runtime lock.'
        }
        if (Test-Path -LiteralPath $NpmPrefix) {
            Remove-Item -Recurse -Force -LiteralPath $NpmPrefix
        }
        New-Item -ItemType Directory -Path $NpmPrefix -Force | Out-Null
        Invoke-NativeChecked -Command $Npm -Arguments @(
            'install', '--global', '--prefix', $NpmPrefix,
            '--ignore-scripts=false', '--allow-scripts', 'openclaw', $Tarball
        ) -Description 'Installation OpenClaw'

        $Marker = Join-Path $NpmPrefix '.openclaw-local-install.json'
        $MarkerTemp = "$Marker.tmp"
        [ordered]@{
            schema_version = '1.0.0'
            openclaw_version = [string]$Lock.openclaw.preferred
            node_version = [string]$Lock.node.preferred
            integrity = [string]$Lock.openclaw.integrity
        } | ConvertTo-Json | Set-Content -LiteralPath $MarkerTemp -Encoding utf8
        Move-Item -LiteralPath $MarkerTemp -Destination $Marker -Force
    }
    finally {
        if (Test-Path -LiteralPath $Temp) {
            Remove-Item -Recurse -Force -LiteralPath $Temp
        }
    }
    if (-not (Test-OpenClawPreferred -NpmPrefix $NpmPrefix)) {
        Write-BootstrapFailure "OpenClaw n'est pas conforme après installation."
    }
}
