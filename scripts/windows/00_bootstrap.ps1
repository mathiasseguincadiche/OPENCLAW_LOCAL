[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$AllowRuntimeDrift
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$LockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
$Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json

function Write-BootstrapFailure([string]$Message) {
    throw "STOP: $Message"
}

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory)][string]$Description
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-BootstrapFailure "$Description (code $LASTEXITCODE)."
    }
}

function Test-PythonPreferred {
    $Preferred = [string]$Lock.python.preferred
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3.13 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" *> $null
        if ($LASTEXITCODE -eq 0) {
            $Version = (& py.exe -3.13 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
            if ($Version -eq $Preferred) {
                return $true
            }
        }
    }
    return $false
}

function Invoke-PreferredPython {
    param([Parameter(Mandatory)][string[]]$Arguments)
    if (-not (Test-PythonPreferred)) {
        Write-BootstrapFailure "Python $($Lock.python.preferred) exact est requis."
    }
    & py.exe -3.13 @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-BootstrapFailure "Python a échoué (code $LASTEXITCODE)."
    }
}

function Install-PythonPreferred {
    if (Test-PythonPreferred) {
        Write-Host "OK  Python $($Lock.python.preferred) déjà présent."
        return
    }
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        Write-BootstrapFailure 'WinGet est requis pour installer Python de façon reproductible.'
    }
    Invoke-NativeChecked -Command 'winget.exe' -Arguments @(
        'install', '--id', 'Python.Python.3.13', '--exact',
        '--version', [string]$Lock.python.preferred,
        '--scope', 'user', '--silent', '--accept-package-agreements', '--accept-source-agreements'
    ) -Description "Installation de Python $($Lock.python.preferred)"
    if (-not (Test-PythonPreferred)) {
        Write-BootstrapFailure "Python $($Lock.python.preferred) reste introuvable après installation."
    }
}

function Test-NodePreferred([string]$NodeHome) {
    $Node = Join-Path $NodeHome 'node.exe'
    if (-not (Test-Path -LiteralPath $Node)) {
        return $false
    }
    return ((& $Node --version 2>$null).Trim() -eq "v$($Lock.node.preferred)")
}

function Install-NodePreferred([string]$RuntimeHome) {
    $NodeHome = Join-Path $RuntimeHome 'node'
    if (Test-NodePreferred $NodeHome) {
        Write-Host "OK  Node.js $($Lock.node.preferred) déjà présent."
        return
    }

    $Version = [string]$Lock.node.preferred
    $Asset = "node-v$Version-win-x64.zip"
    $Uri = "https://nodejs.org/dist/v$Version/$Asset"
    $Temp = Join-Path ([IO.Path]::GetTempPath()) ("openclaw-local-node-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $Temp -Force | Out-Null
    try {
        $Archive = Join-Path $Temp $Asset
        Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $Archive
        $ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash.ToLowerInvariant()
        $ExpectedHash = ([string]$Lock.node.sha256_win_x64_zip).ToLowerInvariant()
        if ($ActualHash -ne $ExpectedHash) {
            Write-BootstrapFailure 'Archive Node.js rejetée: SHA256 différent du runtime lock.'
        }
        Expand-Archive -LiteralPath $Archive -DestinationPath $Temp
        $Expanded = Join-Path $Temp "node-v$Version-win-x64"
        if (Test-Path -LiteralPath $NodeHome) {
            Remove-Item -Recurse -Force -LiteralPath $NodeHome
        }
        New-Item -ItemType Directory -Path $RuntimeHome -Force | Out-Null
        Move-Item -LiteralPath $Expanded -Destination $NodeHome
    }
    finally {
        if (Test-Path -LiteralPath $Temp) {
            Remove-Item -Recurse -Force -LiteralPath $Temp
        }
    }
    if (-not (Test-NodePreferred $NodeHome)) {
        Write-BootstrapFailure 'Node.js n’est pas conforme après installation.'
    }
}

function Test-OpenClawPreferred([string]$NpmPrefix) {
    $PackageJson = Join-Path $NpmPrefix 'node_modules\openclaw\package.json'
    $Command = Join-Path $NpmPrefix 'openclaw.cmd'
    if (-not (Test-Path -LiteralPath $PackageJson) -or -not (Test-Path -LiteralPath $Command)) {
        return $false
    }
    $Installed = [string](Get-Content -Raw -LiteralPath $PackageJson | ConvertFrom-Json).version
    return $Installed -eq [string]$Lock.openclaw.preferred
}

function Install-OpenClawPreferred([string]$RuntimeHome) {
    $NodeHome = Join-Path $RuntimeHome 'node'
    $NpmPrefix = Join-Path $RuntimeHome 'npm-global'
    if (Test-OpenClawPreferred $NpmPrefix) {
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
    if (-not (Test-OpenClawPreferred $NpmPrefix)) {
        Write-BootstrapFailure 'OpenClaw n’est pas conforme après installation.'
    }
}

function Get-OllamaVersion {
    if (-not (Get-Command ollama.exe -ErrorAction SilentlyContinue)) {
        return $null
    }
    $Text = (& ollama.exe --version 2>&1 | Out-String).Trim()
    $Match = [regex]::Match($Text, '(\d+\.\d+\.\d+)')
    if ($Match.Success) {
        return $Match.Groups[1].Value
    }
    return $null
}

function Install-OllamaPreferred {
    param([switch]$AllowDrift)

    $Installed = Get-OllamaVersion
    $Preferred = [string]$Lock.ollama.preferred
    if ($Installed -eq $Preferred) {
        Write-Host "OK  Ollama $Preferred déjà présent."
        return
    }
    if ($Installed -and $AllowDrift) {
        Write-Warning "Ollama $Installed conservé car -AllowRuntimeDrift est actif; qualification obligatoire."
        return
    }
    if ($Installed) {
        Write-BootstrapFailure "Ollama $Installed détecté, mais le lock demande $Preferred. Utilisez -AllowRuntimeDrift pour le conserver explicitement."
    }
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        Write-BootstrapFailure 'WinGet est requis pour installer Ollama.'
    }
    Invoke-NativeChecked -Command 'winget.exe' -Arguments @(
        'install', '--id', [string]$Lock.ollama.winget_id, '--exact',
        '--version', $Preferred, '--scope', 'user', '--silent',
        '--accept-package-agreements', '--accept-source-agreements'
    ) -Description "Installation Ollama $Preferred"
}

function Install-ClawLocalPackage([string]$RuntimeHome) {
    $VenvHome = Join-Path $RuntimeHome 'venv'
    if (-not (Test-Path -LiteralPath (Join-Path $VenvHome 'Scripts\python.exe'))) {
        Invoke-PreferredPython -Arguments @('-m', 'venv', $VenvHome)
    }
    $Python = Join-Path $VenvHome 'Scripts\python.exe'
    Invoke-NativeChecked -Command $Python -Arguments @(
        '-m', 'pip', 'install', '--disable-pip-version-check', 'PyYAML==6.0.2'
    ) -Description 'Installation de PyYAML verrouillé'
    Invoke-NativeChecked -Command $Python -Arguments @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-deps', $RepoRoot
    ) -Description 'Installation de clawlocal'
}

function Invoke-LocalEnvironmentSetup([string]$PlatformRoot, [string]$RuntimeHome) {
    $StateDir = Join-Path $PlatformRoot 'state'
    $NodeHome = Join-Path $RuntimeHome 'node'
    $NpmPrefix = Join-Path $RuntimeHome 'npm-global'
    $VenvScripts = Join-Path $RuntimeHome 'venv\Scripts'
    New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $PlatformRoot 'workspaces') -Force | Out-Null

    $Values = @{
        OPENCLAW_LOCAL_ROOT = $PlatformRoot
        OPENCLAW_STATE_DIR = $StateDir
        OLLAMA_API_KEY = 'ollama-local'
        OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'
    }
    foreach ($Entry in $Values.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($Entry.Key, $Entry.Value, 'User')
        Set-Item -Path "Env:$($Entry.Key)" -Value $Entry.Value
    }

    $CurrentUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $Parts = @($CurrentUserPath -split ';' | Where-Object { $_ })
    foreach ($Wanted in @($NodeHome, $NpmPrefix, $VenvScripts)) {
        if ($Parts -notcontains $Wanted) {
            $Parts += $Wanted
        }
    }
    [Environment]::SetEnvironmentVariable('Path', ($Parts -join ';'), 'User')
    $env:PATH = "$NodeHome;$NpmPrefix;$VenvScripts;$env:PATH"
}

function Test-BootstrapFunctionContract {
    $RequiredFunctions = @(
        'Write-BootstrapFailure',
        'Get-PlatformRoot',
        'Invoke-NativeChecked',
        'Test-PythonPreferred',
        'Invoke-PreferredPython',
        'Install-PythonPreferred',
        'Test-NodePreferred',
        'Install-NodePreferred',
        'Test-OpenClawPreferred',
        'Install-OpenClawPreferred',
        'Get-OllamaVersion',
        'Install-OllamaPreferred',
        'Install-ClawLocalPackage',
        'Invoke-LocalEnvironmentSetup'
    )

    foreach ($FunctionName in $RequiredFunctions) {
        $Function = Get-Command -Name $FunctionName -CommandType Function -ErrorAction SilentlyContinue
        if (-not $Function) {
            Write-BootstrapFailure "Contrat interne invalide: fonction '$FunctionName' absente avant mutation."
        }
    }
}

Test-BootstrapFunctionContract

if (-not $IsWindows) {
    Write-BootstrapFailure 'Windows est requis.'
}
if ($PSVersionTable.PSVersion.Major -lt [int]$Lock.powershell.minimum_major) {
    Write-BootstrapFailure "PowerShell $($Lock.powershell.minimum_major)+ est requis."
}
$Os = Get-CimInstance Win32_OperatingSystem
if ($Os.Caption -notmatch 'Windows 11') {
    Write-BootstrapFailure "Windows 11 requis, détecté: $($Os.Caption)"
}
if ([Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne 'X64') {
    Write-BootstrapFailure 'Architecture x64 requise.'
}

$PlatformRoot = Get-PlatformRoot
$RuntimeHome = Join-Path $PlatformRoot 'runtime'

if ($DryRun) {
    Write-Host '[DRY-RUN] Bootstrap reproductible OPENCLAW_LOCAL'
    Write-Host "Root       : $PlatformRoot"
    Write-Host "Python     : $($Lock.python.preferred)"
    Write-Host "Node.js    : $($Lock.node.preferred)"
    Write-Host "OpenClaw   : $($Lock.openclaw.preferred)"
    Write-Host "Ollama     : $($Lock.ollama.preferred)"
    Write-Host '[DRY-RUN] Aucune installation, aucun téléchargement, aucune variable persistante modifiée.'
    exit 0
}

New-Item -ItemType Directory -Path $RuntimeHome -Force | Out-Null
Install-PythonPreferred
Install-NodePreferred -RuntimeHome $RuntimeHome
Install-OpenClawPreferred -RuntimeHome $RuntimeHome
Install-OllamaPreferred -AllowDrift:$AllowRuntimeDrift
Install-ClawLocalPackage -RuntimeHome $RuntimeHome
Invoke-LocalEnvironmentSetup -PlatformRoot $PlatformRoot -RuntimeHome $RuntimeHome

Write-Host 'OK  Bootstrap OPENCLAW_LOCAL terminé.'
Write-Host 'Fermez puis rouvrez PowerShell pour récupérer le PATH utilisateur dans les nouveaux shells.'
exit 0
