[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$DeployScript = Join-Path $PSScriptRoot '09_deploy_agents.ps1'
$Renderer = Join-Path $RepoRoot 'scripts\26_render_openclaw_config.py'
$RuntimeLockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'

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

function Get-PluginInventory {
    param([Parameter(Mandatory)][string]$OpenClaw)

    $Output = & $OpenClaw 'plugins' 'list' '--json'
    if ($LASTEXITCODE -ne 0) {
        throw "Lecture de l'inventaire plugins OpenClaw en échec (code $LASTEXITCODE)."
    }
    $Text = ($Output | Out-String).Trim()
    try {
        return ($Text | ConvertFrom-Json)
    }
    catch {
        throw 'L''inventaire plugins OpenClaw n''est pas un JSON valide.'
    }
}

function Initialize-ParallelSearchPlugin {
    param(
        [Parameter(Mandatory)][string]$OpenClaw,
        [Parameter(Mandatory)][string]$LockPath
    )

    if (-not (Test-Path -LiteralPath $LockPath)) {
        throw "Contrat runtime introuvable: $LockPath"
    }
    $Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json
    $Parallel = $Lock.openclaw.plugins.parallel
    $PluginId = 'parallel'
    $Package = [string]$Parallel.package
    $Version = [string]$Parallel.preferred
    $Provider = [string]$Parallel.provider
    if (-not $Package -or -not $Version -or $Provider -ne 'parallel-free') {
        throw 'Contrat Parallel invalide dans runtime_versions.json.'
    }

    $Inventory = Get-PluginInventory -OpenClaw $OpenClaw
    $Plugin = @($Inventory.plugins | Where-Object { [string]$_.id -eq $PluginId })
    if ($Plugin.Count -eq 0) {
        $Spec = "npm:$Package@$Version"
        Write-Host "Installation du plugin Web requis : $Spec"
        Invoke-Checked -Command $OpenClaw -Arguments @(
            'plugins', 'install', $Spec, '--pin'
        ) -Description 'Installation du plugin Parallel'
        $Inventory = Get-PluginInventory -OpenClaw $OpenClaw
        $Plugin = @($Inventory.plugins | Where-Object { [string]$_.id -eq $PluginId })
    }
    if ($Plugin.Count -eq 0) {
        throw 'Plugin Parallel absent après installation.'
    }

    if (-not [bool]$Plugin[0].enabled) {
        Invoke-Checked -Command $OpenClaw -Arguments @(
            'plugins', 'enable', $PluginId
        ) -Description 'Activation du plugin Parallel'
        $Inventory = Get-PluginInventory -OpenClaw $OpenClaw
        $Plugin = @($Inventory.plugins | Where-Object { [string]$_.id -eq $PluginId })
    }
    if ($Plugin.Count -eq 0 -or -not [bool]$Plugin[0].enabled) {
        throw 'Plugin Parallel installé mais non activé.'
    }

    $RuntimeProbe = & $OpenClaw 'plugins' 'inspect' $PluginId '--runtime' '--json'
    if ($LASTEXITCODE -ne 0) {
        throw "Chargement runtime du plugin Parallel en échec (code $LASTEXITCODE)."
    }
    try {
        $null = (($RuntimeProbe | Out-String).Trim() | ConvertFrom-Json)
    }
    catch {
        throw 'Le diagnostic runtime du plugin Parallel n''est pas un JSON valide.'
    }
    Write-Host "OK  Plugin Parallel $Version actif pour le provider $Provider."
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$SystemWorkspace = Join-Path $PlatformRoot 'workspaces\system'
$GeneratedDir = Join-Path $PlatformRoot 'runtime\generated'
$PatchPath = Join-Path $GeneratedDir 'openclaw.local.patch.json'
$SchemaPath = Join-Path $GeneratedDir 'openclaw.schema.json'

if ($DryRun) {
    Write-Host '[DRY-RUN] Configuration OpenClaw local-first'
    Write-Host "State      : $StateDir"
    Write-Host "Workspaces : $(Join-Path $PlatformRoot 'workspaces')"
    Write-Host "Patch      : $PatchPath"
    Write-Host "Schema     : $SchemaPath"
    Write-Host '[DRY-RUN] Vérifier/installer le plugin Parallel versionné, déployer 8 agents, capturer le schéma vivant, valider le patch puis l''appliquer en mode réel.'
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
New-Item -ItemType Directory -Path $GeneratedDir -Force | Out-Null

$ConfigPath = Join-Path $StateDir 'openclaw.json'
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Invoke-Checked -Command $OpenClaw -Arguments @(
        'setup', '--baseline', '--workspace', $SystemWorkspace
    ) -Description 'Initialisation baseline OpenClaw'
}

Initialize-ParallelSearchPlugin -OpenClaw $OpenClaw -LockPath $RuntimeLockPath

$SchemaOutput = & $OpenClaw 'config' 'schema'
if ($LASTEXITCODE -ne 0) {
    throw "Lecture du schéma OpenClaw en échec (code $LASTEXITCODE)."
}
$SchemaText = ($SchemaOutput | Out-String).Trim()
try {
    $null = $SchemaText | ConvertFrom-Json
}
catch {
    throw 'Le schéma OpenClaw retourné par la CLI n''est pas un JSON valide.'
}
Set-Content -LiteralPath $SchemaPath -Value $SchemaText -Encoding utf8
Write-Host "OPENCLAW_SCHEMA=$SchemaPath"

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
