[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$DeployScript = Join-Path $PSScriptRoot '09_deploy_agents.ps1'
$Renderer = Join-Path $RepoRoot 'scripts\26_render_openclaw_config.py'

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
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
    throw 'OpenClaw est absent. Exécutez en premier .\menu.ps1 -Action install-core.'
}

function Get-PythonCommand([string]$PlatformRoot) {
    $Managed = Join-Path $PlatformRoot 'runtime\venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $Managed) {
        return $Managed
    }
    $Found = Get-Command python -ErrorAction SilentlyContinue
    if ($Found) {
        return $Found.Source
    }
    throw 'Python clawlocal est absent. Exécutez en premier install-core.'
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Description
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description (code $LASTEXITCODE)."
    }
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$SystemWorkspace = Join-Path $PlatformRoot 'workspaces\system'
$PatchPath = Join-Path $PlatformRoot 'runtime\generated\openclaw.local.patch.json'

if ($DryRun) {
    Write-Host '[DRY-RUN] Configuration OpenClaw local-first'
    Write-Host "State      : $StateDir"
    Write-Host "Workspaces : $(Join-Path $PlatformRoot 'workspaces')"
    Write-Host "Patch      : $PatchPath"
    Write-Host '[DRY-RUN] Déploiement de 8 agents, validation config patch, puis application atomique en mode réel.'
    exit 0
}

$env:OPENCLAW_LOCAL_ROOT = $PlatformRoot
$env:OPENCLAW_STATE_DIR = $StateDir
$env:OLLAMA_API_KEY = 'ollama-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

$OpenClaw = Get-OpenClawCommand $PlatformRoot
$Python = Get-PythonCommand $PlatformRoot
New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
New-Item -ItemType Directory -Path $SystemWorkspace -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $PatchPath) -Force | Out-Null

$ConfigPath = Join-Path $StateDir 'openclaw.json'
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Invoke-Checked -Command $OpenClaw -Arguments @(
        'setup', '--baseline', '--workspace', $SystemWorkspace
    ) -Description 'Initialisation baseline OpenClaw'
}

& $DeployScript
if ($LASTEXITCODE -ne 0) {
    throw 'Déploiement des workspaces agents en échec.'
}

Invoke-Checked -Command $Python -Arguments @(
    $Renderer, '--platform-root', $PlatformRoot, '--output', $PatchPath
) -Description 'Génération du patch OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'patch', '--file', $PatchPath, '--dry-run'
) -Description 'Validation dry-run du patch OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'patch', '--file', $PatchPath
) -Description 'Application du patch OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'validate', '--json'
) -Description 'Validation finale de la configuration OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'agents', 'list', '--json'
) -Description 'Lecture de la flotte OpenClaw'

Write-Host 'OK  Configuration OpenClaw et flotte de 8 agents appliquées.'
exit 0
