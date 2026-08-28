[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$AllowRuntimeDrift,
    [switch]$SkipGatewayService
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$env:OPENCLAW_LOCAL_REPO_ROOT = $RepoRoot
$Bootstrap = Join-Path $PSScriptRoot '00_bootstrap.ps1'
$ConfigureOllama = Join-Path $PSScriptRoot '02_configure_local.ps1'
$PullModels = Join-Path $PSScriptRoot '03_pull_models.ps1'
$ConfigureOpenClaw = Join-Path $PSScriptRoot '08_configure_openclaw.ps1'
$VerifyLocal = Join-Path $PSScriptRoot '04_verify_local.ps1'

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Invoke-ScriptChecked {
    param(
        [Parameter(Mandatory)][string]$Path,
        [hashtable]$Parameters = @{},
        [Parameter(Mandatory)][string]$Description
    )
    & $Path @Parameters
    if ($LASTEXITCODE -ne 0) {
        throw "$Description (code $LASTEXITCODE)."
    }
}

function Get-OpenClawCommand([string]$PlatformRoot) {
    $Found = Get-Command openclaw -ErrorAction SilentlyContinue
    if ($Found) {
        return $Found.Source
    }
    $Managed = Join-Path $PlatformRoot 'runtime\npm-global\openclaw.cmd'
    if (Test-Path -LiteralPath $Managed) {
        return $Managed
    }
    throw 'OpenClaw est introuvable après bootstrap.'
}

if ($DryRun) {
    Invoke-ScriptChecked -Path $Bootstrap -Parameters @{
        DryRun = $true
        AllowRuntimeDrift = $AllowRuntimeDrift
    } -Description 'Dry-run bootstrap'
    Invoke-ScriptChecked -Path $ConfigureOllama -Parameters @{ DryRun = $true } `
        -Description 'Dry-run Ollama'
    Invoke-ScriptChecked -Path $PullModels -Parameters @{ DryRun = $true } `
        -Description 'Dry-run modèles'
    Invoke-ScriptChecked -Path $ConfigureOpenClaw -Parameters @{ DryRun = $true } `
        -Description 'Dry-run OpenClaw'
    Write-Host '[DRY-RUN] Gateway service: install/start en mode réel uniquement.'
    Write-Host '[DRY-RUN] Aucune mutation réalisée.'
    exit 0
}

Invoke-ScriptChecked -Path $Bootstrap -Parameters @{
    AllowRuntimeDrift = $AllowRuntimeDrift
} -Description 'Bootstrap runtime'
Invoke-ScriptChecked -Path $ConfigureOllama -Description 'Configuration Ollama'
Invoke-ScriptChecked -Path $PullModels -Description 'Téléchargement des modèles'
Invoke-ScriptChecked -Path $ConfigureOpenClaw -Description 'Configuration OpenClaw'

$PlatformRoot = Get-PlatformRoot
$OpenClaw = Get-OpenClawCommand $PlatformRoot
$env:OPENCLAW_STATE_DIR = Join-Path $PlatformRoot 'state'
$env:OLLAMA_API_KEY = 'ollama-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

if (-not $SkipGatewayService) {
    & $OpenClaw gateway install --runtime node --force --json
    if ($LASTEXITCODE -ne 0) {
        throw 'Installation du service Gateway OpenClaw en échec.'
    }
    & $OpenClaw gateway start --json
    if ($LASTEXITCODE -ne 0) {
        throw 'Démarrage du service Gateway OpenClaw en échec.'
    }
    & $OpenClaw gateway status --require-rpc --json
    if ($LASTEXITCODE -ne 0) {
        throw 'Gateway OpenClaw installé mais non joignable.'
    }
}

Invoke-ScriptChecked -Path $VerifyLocal -Description 'Vérification Ollama'
Write-Host 'OK  Installation complète OPENCLAW_LOCAL terminée.'
Write-Host "Repo: $RepoRoot"
Write-Host 'Étape suivante: .\menu.ps1 -Action e2e puis .\menu.ps1 -Action qualification.'
exit 0
