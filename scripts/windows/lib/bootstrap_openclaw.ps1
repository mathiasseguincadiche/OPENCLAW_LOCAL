Set-StrictMode -Version Latest

function Test-OpenClawPreferred {
    param([Parameter(Mandatory)][string]$NpmPrefix)

    $PackageJson = Join-Path $NpmPrefix 'node_modules\openclaw\package.json'
    $Command = Join-Path $NpmPrefix 'openclaw.cmd'
    if (-not (Test-Path -LiteralPath $PackageJson) -or -not (Test-Path -LiteralPath $Command)) {
        return $false
    }
    $Installed = [string](Get-Content -Raw -LiteralPath $PackageJson | ConvertFrom-Json).version
    return $Installed -eq [string]$Lock.openclaw.preferred
}

function Install-OpenClawPreferred {
    param([Parameter(Mandatory)][string]$RuntimeHome)

    $NodeHome = Join-Path $RuntimeHome 'node'
    $NpmPrefix = Join-Path $RuntimeHome 'npm-global'
    if (Test-OpenClawPreferred -NpmPrefix $NpmPrefix) {
        Write-Host "OK  OpenClaw $($Lock.openclaw.preferred) déjà présent."
        return
    }

    $Npm = Join-Path $NodeHome 'npm.cmd'
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
            'install', '--global', '--prefix', $NpmPrefix, '--ignore-scripts=false', $Tarball
        ) -Description 'Installation OpenClaw'
    }
    finally {
        if (Test-Path -LiteralPath $Temp) {
            Remove-Item -Recurse -Force -LiteralPath $Temp
        }
    }
    if (-not (Test-OpenClawPreferred -NpmPrefix $NpmPrefix)) {
        Write-BootstrapFailure 'OpenClaw n’est pas conforme après installation.'
    }
}
