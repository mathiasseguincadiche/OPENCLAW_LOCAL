[CmdletBinding()]
param(
    [switch]$DryRun,
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Catalog = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot 'config\v1\model_catalog.yaml')
$AgentIds = @(
    'chef-operations',
    'expert-recherche',
    'architecte-solutions',
    'ingenieur-devops',
    'ingenieur-securite',
    'ingenieur-release-forges',
    'redacteur-technique',
    'auditeur-qualite'
)

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
    throw 'OpenClaw absent. Exécutez install-core.'
}

function Invoke-OpenClawJson {
    param(
        [Parameter(Mandatory)][string]$OpenClaw,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Description
    )
    $Output = & $OpenClaw @Arguments 2>&1
    $ExitCode = $LASTEXITCODE
    $Text = ($Output | Out-String).Trim()
    if ($ExitCode -ne 0) {
        throw "$Description en échec (code $ExitCode): $Text"
    }
    try {
        return $Text | ConvertFrom-Json
    }
    catch {
        throw "$Description n'a pas renvoyé un JSON valide: $Text"
    }
}

function Test-OllamaProvider([object]$Payload, [string]$Description) {
    $Json = $Payload | ConvertTo-Json -Depth 50 -Compress
    if ($Json -notmatch '"provider"\s*:\s*"ollama"') {
        throw "$Description n'apporte pas de preuve provider=ollama. Aucun fallback cloud n'est accepté."
    }
    return $true
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$ProofsRoot = Join-Path $PlatformRoot 'proofs'
$ScratchRoot = Join-Path $PlatformRoot 'runtime\e2e-scratch'
$ConfigPath = Join-Path $StateDir 'openclaw.json'
$QwenModel = if ($Catalog -match 'runtime_id:\s*"(qwen3\.5:9b)"') {
    $Matches[1]
}
else {
    'qwen3.5:9b'
}

if ($DryRun) {
    Write-Host '[DRY-RUN] E2E OpenClaw'
    Write-Host '[DRY-RUN] 8 agents -> Gateway -> Ollama'
    Write-Host '[DRY-RUN] agent exec -> tool write'
    Write-Host '[DRY-RUN] erreur outil contrôlée -> réparation'
    Write-Host '[DRY-RUN] 3 runs de stabilité'
    Write-Host '[DRY-RUN] aucune escalade cloud'
    exit 0
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw 'Configuration OpenClaw absente. Exécutez configure-openclaw.'
}
$OpenClaw = Get-OpenClawCommand $PlatformRoot
$env:OPENCLAW_STATE_DIR = $StateDir
$env:OLLAMA_API_KEY = 'ollama-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

$null = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'config', 'validate', '--json'
) -Description 'Validation config'
$null = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'gateway', 'status', '--require-rpc', '--json'
) -Description 'Gateway OpenClaw'

$Evidence = [ordered]@{
    schema_version = '1.0.0'
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    platform_root = $PlatformRoot
    cloud_enabled = $false
    agent_smoke = @()
    tool_call = $null
    tool_feedback_repair = $null
    stability = @()
}

foreach ($AgentId in $AgentIds) {
    $Prompt = "Réponds en une ligne avec exactement: AGENT_OK $AgentId"
    $Result = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
        'agent', '--agent', $AgentId, '--message', $Prompt,
        '--timeout', [string]$TimeoutSeconds, '--json'
    ) -Description "Smoke agent $AgentId"
    $null = Test-OllamaProvider -Payload $Result -Description "Smoke agent $AgentId"
    $Evidence.agent_smoke += [ordered]@{ agent = $AgentId; result = $Result }
}

if (Test-Path -LiteralPath $ScratchRoot) {
    Remove-Item -Recurse -Force -LiteralPath $ScratchRoot
}
New-Item -ItemType Directory -Path $ScratchRoot -Force | Out-Null

$ToolPrompt = @'
Utilise réellement l'outil d'écriture disponible. Crée le fichier tool-call-ok.txt dans le répertoire de travail avec exactement le texte TOOL_OK. Ensuite réponds TOOL_OK.
'@
$ToolResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'agent', 'exec', $ToolPrompt, '--cwd', $ScratchRoot,
    '--model', "ollama/$QwenModel", '--code-mode', 'code', '--local-model-lean',
    '--auth-env-only', '--timeout', [string]$TimeoutSeconds, '--json'
) -Description 'Tool-calling OpenClaw/Ollama'
$null = Test-OllamaProvider -Payload $ToolResult -Description 'Tool-calling OpenClaw/Ollama'
$ToolMarker = Join-Path $ScratchRoot 'tool-call-ok.txt'
if (-not (Test-Path -LiteralPath $ToolMarker)) {
    throw 'Le modèle n’a pas créé le marqueur tool-call-ok.txt.'
}
if ((Get-Content -Raw -LiteralPath $ToolMarker).Trim() -ne 'TOOL_OK') {
    throw 'Le contenu du marqueur tool-call-ok.txt est incorrect.'
}
$Evidence.tool_call = $ToolResult

Set-Content -LiteralPath (Join-Path $ScratchRoot 'fallback.txt') -Value 'FALLBACK_OK' -Encoding utf8
$RepairPrompt = @'
Teste d'abord la lecture du fichier missing-intentional.txt, qui n'existe pas. Après l'erreur de l'outil, corrige ton plan: lis fallback.txt, puis crée repair-ok.txt avec exactement REPAIRED. Ne fabrique pas le résultat du premier outil.
'@
$RepairResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'agent', 'exec', $RepairPrompt, '--cwd', $ScratchRoot,
    '--model', "ollama/$QwenModel", '--code-mode', 'code', '--local-model-lean',
    '--auth-env-only', '--timeout', [string]$TimeoutSeconds, '--json'
) -Description 'Réparation après erreur outil'
$null = Test-OllamaProvider -Payload $RepairResult -Description 'Réparation après erreur outil'
$RepairMarker = Join-Path $ScratchRoot 'repair-ok.txt'
if (-not (Test-Path -LiteralPath $RepairMarker)) {
    throw 'Le scénario de réparation n’a pas créé repair-ok.txt.'
}
if ((Get-Content -Raw -LiteralPath $RepairMarker).Trim() -ne 'REPAIRED') {
    throw 'Le contenu de repair-ok.txt est incorrect.'
}
$Evidence.tool_feedback_repair = $RepairResult

for ($Run = 1; $Run -le 3; $Run++) {
    $StableResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
        'agent', 'exec', "Réponds exactement STABLE_$Run", '--cwd', $ScratchRoot,
        '--model', "ollama/$QwenModel", '--auth-env-only',
        '--timeout', [string]$TimeoutSeconds, '--json'
    ) -Description "Stabilité run $Run"
    $null = Test-OllamaProvider -Payload $StableResult -Description "Stabilité run $Run"
    if ([string]$StableResult.final -notmatch "STABLE_$Run") {
        throw "Stabilité run $Run: réponse finale inattendue."
    }
    $Evidence.stability += $StableResult
}

New-Item -ItemType Directory -Path $ProofsRoot -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ProofPath = Join-Path $ProofsRoot "openclaw_e2e_$Stamp.json"
$Evidence | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $ProofPath -Encoding utf8
Write-Host "OK  E2E OpenClaw terminé: $ProofPath"
Write-Host 'Ce succès ne promeut aucun modèle automatiquement; revue humaine et qualification matérielle restent requises.'
exit 0
