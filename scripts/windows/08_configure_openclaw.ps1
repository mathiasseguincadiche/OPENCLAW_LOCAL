[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateSet('ollama-vulkan', 'llama-cpp-sycl', 'b580-hybrid')]
    [string]$Backend = 'ollama-vulkan'
)

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

function Test-OllamaReady {
    try {
        $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
    }
    catch {
        throw "Backend Ollama non prêt: $($_.Exception.Message)"
    }
}

function Test-LlamaCppInventory {
    param(
        [Parameter(Mandatory)][string]$Endpoint,
        [Parameter(Mandatory)][string[]]$Expected,
        [Parameter(Mandatory)][string]$Label
    )

    try {
        $Inventory = Invoke-RestMethod -Method Get -Uri "$Endpoint/models?reload=1" -TimeoutSec 10
    }
    catch {
        throw "$Label non prêt sur $Endpoint. Détail: $($_.Exception.Message)"
    }
    $Ids = @($Inventory.data | ForEach-Object { [string]$_.id })
    foreach ($Model in $Expected) {
        if (-not ($Ids | Where-Object { $_ -ieq $Model })) {
            throw "$Label actif mais modèle requis absent: $Model (disponibles=$($Ids -join ','))."
        }
    }
}

function Test-SelectedBackendReady {
    param(
        [Parameter(Mandatory)][string]$BackendId,
        [Parameter(Mandatory)][string]$LockPath
    )

    if ($BackendId -eq 'ollama-vulkan') {
        Test-OllamaReady
        Write-Host 'OK  Backend texte sélectionné: ollama-vulkan.'
        return
    }

    $Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json
    if ($BackendId -eq 'llama-cpp-sycl') {
        Test-LlamaCppInventory -Endpoint ([string]$Lock.llama_cpp_sycl.endpoint) `
            -Expected @(
                'qwen3.5:9b-q4_K_M',
                'gemma3:12b-it-q4_K_M',
                'qwen2.5-coder:14b-instruct-q4_K_M'
            ) `
            -Label 'Backend Intel SYCL'
        Write-Host 'OK  Backend texte sélectionné: llama-cpp-sycl (provider OpenClaw intel-sycl).'
        Write-Host 'INFO Image/PDF restent sur Ollama tant que le multimodal SYCL n''est pas qualifié.'
        return
    }

    if ($BackendId -eq 'b580-hybrid') {
        Test-OllamaReady
        Test-LlamaCppInventory -Endpoint ([string]$Lock.llama_cpp_vulkan.endpoint) `
            -Expected @($Lock.llama_cpp_vulkan.managed_models | ForEach-Object { [string]$_ }) `
            -Label 'Backend Intel Vulkan géré'
        Write-Host 'OK  Profil B580 hybride prêt: Qwen 3.5->Ollama, Gemma 3/Qwen Coder->intel-vulkan.'
        Write-Host 'INFO Image/PDF restent intégralement sur Ollama via Qwen 3.5/Gemma 3.'
        return
    }

    throw "Backend OpenClaw non géré par le configurateur: $BackendId"
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$SystemWorkspace = Join-Path $PlatformRoot 'workspaces\system'
$GeneratedDir = Join-Path $PlatformRoot 'runtime\generated'
$PatchPath = Join-Path $GeneratedDir "openclaw.$Backend.patch.json"
$SchemaPath = Join-Path $GeneratedDir 'openclaw.schema.json'

if ($DryRun) {
    Write-Host '[DRY-RUN] Configuration OpenClaw local-first'
    Write-Host "Backend    : $Backend"
    Write-Host "State      : $StateDir"
    Write-Host "Workspaces : $(Join-Path $PlatformRoot 'workspaces')"
    Write-Host "Patch      : $PatchPath"
    Write-Host "Schema     : $SchemaPath"
    if ($Backend -eq 'llama-cpp-sycl') {
        Write-Host '[DRY-RUN] Exiger le routeur Intel SYCL prêt avec les trois modèles; texte -> intel-sycl; image/PDF -> Ollama.'
        Write-Host '[DRY-RUN] Rollback explicite: .\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan'
    }
    elseif ($Backend -eq 'b580-hybrid') {
        Write-Host '[DRY-RUN] Exiger Ollama + routeur Intel Vulkan géré prêt.'
        Write-Host '[DRY-RUN] Routage texte: Qwen 3.5 -> Ollama; Gemma 3 + Qwen Coder -> intel-vulkan; image/PDF -> Ollama.'
        Write-Host '[DRY-RUN] Contexte nominal B580: 8192 tokens; 16384 reste un contexte de qualification.'
        Write-Host '[DRY-RUN] Rollback explicite: .\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan'
    }
    Write-Host '[DRY-RUN] Migration gérée: les listes contractuelles OpenClaw (dont models.providers.*.models et agents.list) sont remplacées intentionnellement avec --replace afin de retirer les anciens IDs.'
    Write-Host '[DRY-RUN] Vérifier/installer Parallel, déployer 8 agents, capturer le schéma vivant, valider le patch avec --replace puis l''appliquer.'
    exit 0
}

$env:OPENCLAW_LOCAL_ROOT = $PlatformRoot
$env:OPENCLAW_STATE_DIR = $StateDir
$env:OLLAMA_API_KEY = 'ollama-local'
$env:INTEL_SYCL_API_KEY = 'intel-sycl-local'
$env:INTEL_VULKAN_API_KEY = 'intel-vulkan-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

Test-SelectedBackendReady -BackendId $Backend -LockPath $RuntimeLockPath

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
    $Renderer, '--platform-root', $PlatformRoot, '--backend', $Backend, '--output', $PatchPath
) -Description 'Génération du patch OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'patch', '--file', $PatchPath, '--dry-run', '--replace'
) -Description 'Validation dry-run du patch OpenClaw avec remplacement des listes gérées'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'patch', '--file', $PatchPath, '--replace'
) -Description 'Application du patch OpenClaw avec remplacement des listes gérées'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'config', 'validate', '--json'
) -Description 'Validation finale de la configuration OpenClaw'

Invoke-Checked -Command $OpenClaw -Arguments @(
    'agents', 'list', '--json'
) -Description 'Lecture de la flotte OpenClaw'

Write-Host "OK  Configuration OpenClaw appliquée: backend texte=$Backend, 8 agents."
if ($Backend -in @('llama-cpp-sycl', 'b580-hybrid')) {
    Write-Host 'INFO Rollback: .\menu.ps1 -Action configure-openclaw -Backend ollama-vulkan'
}
exit 0
