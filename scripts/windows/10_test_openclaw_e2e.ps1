[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateSet('ollama-vulkan', 'llama-cpp-sycl', 'b580-hybrid')]
    [string]$Backend = 'ollama-vulkan',
    [int]$TimeoutSeconds = 180,
    [ValidateRange(5, 300)][int]$GatewayReadyTimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ListModels = Join-Path $RepoRoot 'scripts\20_list_models.py'
$GatewayHealth = Join-Path $PSScriptRoot 'lib\gateway_health.ps1'
$RuntimeLockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
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
$ToolAgentId = 'ingenieur-devops'

if (-not (Test-Path -LiteralPath $GatewayHealth)) {
    throw "Bibliothèque de santé Gateway introuvable: $GatewayHealth"
}
. $GatewayHealth

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

    $Started = [DateTimeOffset]::UtcNow
    Write-Host "E2E  START $Description (timeout appel=${TimeoutSeconds}s)"
    $Output = & $OpenClaw @Arguments 2>&1
    $ExitCode = $LASTEXITCODE
    $Text = ($Output | Out-String).Trim()
    if ($ExitCode -ne 0) {
        throw "$Description en échec (code $ExitCode): $Text"
    }
    try {
        $Parsed = $Text | ConvertFrom-Json
    }
    catch {
        throw "$Description n'a pas renvoyé un JSON valide: $Text"
    }
    $Elapsed = ([DateTimeOffset]::UtcNow - $Started).TotalSeconds
    Write-Host ("E2E  PASS  {0} ({1:N1} s)" -f $Description, $Elapsed)
    return $Parsed
}

function Test-ExpectedProvider {
    param(
        [Parameter(Mandatory)][object]$Payload,
        [Parameter(Mandatory)][string]$ExpectedProvider,
        [Parameter(Mandatory)][string]$Description
    )
    $Json = $Payload | ConvertTo-Json -Depth 50 -Compress
    $Pattern = '"provider"\s*:\s*"' + [regex]::Escape($ExpectedProvider) + '"'
    if ($Json -notmatch $Pattern) {
        throw (
            "$Description n'apporte pas de preuve provider=$ExpectedProvider. " +
            'Aucun fallback de backend ou cloud silencieux n''est accepté.'
        )
    }
    return $true
}

function Test-GatewayTransport {
    param(
        [Parameter(Mandatory)][object]$Payload,
        [Parameter(Mandatory)][string]$Description
    )
    $Json = $Payload | ConvertTo-Json -Depth 50 -Compress
    if (
        $Json -match '"fallbackFrom"\s*:\s*"gateway"' -or
        $Json -match '"transport"\s*:\s*"embedded"'
    ) {
        throw (
            "$Description a quitté silencieusement le transport Gateway. " +
            'Le E2E exige le chemin réellement configuré.'
        )
    }
    return $true
}

function Get-OpenClawText {
    param([Parameter(Mandatory)][object]$Payload)

    $FinalProperty = $Payload.PSObject.Properties['final']
    if ($FinalProperty -and -not [string]::IsNullOrWhiteSpace([string]$FinalProperty.Value)) {
        return [string]$FinalProperty.Value
    }
    $PayloadsProperty = $Payload.PSObject.Properties['payloads']
    if ($PayloadsProperty) {
        $Texts = @(
            $PayloadsProperty.Value | ForEach-Object {
                $TextProperty = $_.PSObject.Properties['text']
                if ($TextProperty -and -not [string]::IsNullOrWhiteSpace([string]$TextProperty.Value)) {
                    [string]$TextProperty.Value
                }
            }
        )
        if ($Texts.Count -gt 0) {
            return ($Texts -join "`n")
        }
    }
    return ''
}

function Get-ProviderFromModelRef {
    param([Parameter(Mandatory)][string]$ModelRef)
    if ($ModelRef -notmatch '^([^/]+)/') {
        throw "Référence modèle OpenClaw invalide: $ModelRef"
    }
    return $Matches[1]
}

function Get-AgentEntry {
    param(
        [Parameter(Mandatory)]$Config,
        [Parameter(Mandatory)][string]$AgentId
    )
    $Entry = @($Config.agents.list | Where-Object { [string]$_.id -eq $AgentId }) |
        Select-Object -First 1
    if (-not $Entry) {
        throw "Agent absent de la configuration OpenClaw: $AgentId"
    }
    return $Entry
}

function Get-AgentPrimaryModelRef {
    param(
        [Parameter(Mandatory)]$Config,
        [Parameter(Mandatory)][string]$AgentId
    )
    $Entry = Get-AgentEntry -Config $Config -AgentId $AgentId
    return [string]$Entry.model.primary
}

function Get-AgentWorkspace {
    param(
        [Parameter(Mandatory)]$Config,
        [Parameter(Mandatory)][string]$AgentId
    )
    $Entry = Get-AgentEntry -Config $Config -AgentId $AgentId
    $Workspace = [string]$Entry.workspace
    if ([string]::IsNullOrWhiteSpace($Workspace)) {
        throw "Workspace OpenClaw absent pour l'agent: $AgentId"
    }
    return $Workspace
}

function Test-HybridRuntimeReady {
    param([Parameter(Mandatory)]$Lock)

    try {
        $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
    }
    catch {
        throw "Ollama non prêt avant E2E hybride: $($_.Exception.Message)"
    }
    $Endpoint = [string]$Lock.llama_cpp_vulkan.endpoint
    try {
        $Inventory = Invoke-RestMethod -Method Get -Uri "$Endpoint/models?reload=1" -TimeoutSec 10
    }
    catch {
        throw "Backend Intel Vulkan non prêt avant E2E hybride: $($_.Exception.Message)"
    }
    $Ids = @($Inventory.data | ForEach-Object { [string]$_.id })
    foreach ($Model in @($Lock.llama_cpp_vulkan.managed_models | ForEach-Object { [string]$_ })) {
        if (-not ($Ids | Where-Object { $_ -ieq $Model })) {
            throw "Backend Intel Vulkan incomplet avant E2E: modèle absent $Model"
        }
    }
}

$ExpectedProviderLabel = if ($Backend -eq 'llama-cpp-sycl') {
    'intel-sycl'
}
elseif ($Backend -eq 'b580-hybrid') {
    'mixed-local'
}
else {
    'ollama'
}

if ($DryRun) {
    Write-Host '[DRY-RUN] E2E OpenClaw'
    Write-Host "[DRY-RUN] backend texte=$Backend provider attendu=$ExpectedProviderLabel"
    Write-Host '[DRY-RUN] provider agent déduit de la référence primary effectivement configurée.'
    Write-Host "[DRY-RUN] readiness Gateway RPC bornée à ${GatewayReadyTimeoutSeconds}s"
    Write-Host '[DRY-RUN] 8 agents -> Gateway -> provider local attendu sans fallback silencieux.'
    if ($Backend -eq 'b580-hybrid') {
        Write-Host '[DRY-RUN] Qwen -> Ollama; Gemma/Devstral -> intel-vulkan; tool-call Devstral/Vulkan obligatoire.'
    }
    Write-Host '[DRY-RUN] tool-calling via ingenieur-devops dans son workspace borné.'
    Write-Host '[DRY-RUN] compatibilité CLI OpenClaw 2026.7.1-2: agent --agent/--model/--message.'
    Write-Host '[DRY-RUN] erreur outil contrôlée -> réparation'
    Write-Host '[DRY-RUN] 3 runs de stabilité'
    Write-Host '[DRY-RUN] progression visible pour chaque appel long.'
    Write-Host '[DRY-RUN] aucune escalade cloud ni fallback de provider/transport.'
    exit 0
}

$RequiredModels = @(& python $ListModels --provider ollama --required)
if ($LASTEXITCODE -ne 0) {
    throw 'Impossible de lire model_catalog.yaml.'
}
$RequiredModels = @($RequiredModels | Where-Object { $_ -and $_.Trim() })
if ($RequiredModels.Count -eq 0) {
    throw 'Aucun modèle required local dans model_catalog.yaml.'
}
$PrimaryModel = $RequiredModels[0]
$ModelRef = if ($Backend -eq 'llama-cpp-sycl') {
    "intel-sycl/$PrimaryModel"
}
else {
    "ollama/$PrimaryModel"
}

$RuntimeLock = Get-Content -Raw -LiteralPath $RuntimeLockPath | ConvertFrom-Json
if ($Backend -eq 'llama-cpp-sycl') {
    try {
        $SyclModels = Invoke-RestMethod -Method Get `
            -Uri 'http://127.0.0.1:8080/v1/models?reload=1' -TimeoutSec 10
    }
    catch {
        throw "Backend Intel SYCL non prêt avant E2E: $($_.Exception.Message)"
    }
    $SyclIds = @($SyclModels.data | ForEach-Object { [string]$_.id })
    foreach ($RequiredModel in $RequiredModels) {
        if (-not ($SyclIds | Where-Object { $_ -ieq $RequiredModel })) {
            throw "Backend Intel SYCL incomplet avant E2E: modèle absent $RequiredModel"
        }
    }
}
elseif ($Backend -eq 'b580-hybrid') {
    Test-HybridRuntimeReady -Lock $RuntimeLock
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$ProofsRoot = Join-Path $PlatformRoot 'proofs'
$ConfigPath = Join-Path $StateDir 'openclaw.json'

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw 'Configuration OpenClaw absente. Exécutez configure-openclaw.'
}
$Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
$OpenClaw = Get-OpenClawCommand $PlatformRoot
$env:OPENCLAW_STATE_DIR = $StateDir
$env:OLLAMA_API_KEY = 'ollama-local'
$env:INTEL_SYCL_API_KEY = 'intel-sycl-local'
$env:INTEL_VULKAN_API_KEY = 'intel-vulkan-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

$ExpectedOpenClawVersion = [string]$RuntimeLock.openclaw.preferred
$ActualOpenClawVersion = (& $OpenClaw '--version' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Impossible de lire la version OpenClaw: $ActualOpenClawVersion"
}
if ($ActualOpenClawVersion -notmatch [regex]::Escape($ExpectedOpenClawVersion)) {
    throw (
        "Runtime OpenClaw inattendu. Attendu=$ExpectedOpenClawVersion " +
        "Reçu=$ActualOpenClawVersion"
    )
}
Write-Host "OK  OpenClaw verrouillé: $ActualOpenClawVersion"

$RunStamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$SessionPrefix = "e2e-$RunStamp"
$ToolWorkspace = Get-AgentWorkspace -Config $Config -AgentId $ToolAgentId
$ScratchRelative = ".openclaw-e2e\$RunStamp"
$ScratchPromptPath = $ScratchRelative -replace '\\', '/'
$ScratchRoot = Join-Path $ToolWorkspace $ScratchRelative
if (Test-Path -LiteralPath $ScratchRoot) {
    Remove-Item -Recurse -Force -LiteralPath $ScratchRoot
}
New-Item -ItemType Directory -Path $ScratchRoot -Force | Out-Null
Write-Host "E2E  Workspace outils=$ToolWorkspace"
Write-Host "E2E  Scratch borné=$ScratchRoot"

$null = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'config', 'validate', '--json'
) -Description 'Validation config'

Write-Host "E2E  START Gateway readiness (max=${GatewayReadyTimeoutSeconds}s)"
$GatewayReadiness = Wait-OpenClawGatewayReady -OpenClaw $OpenClaw `
    -TimeoutSeconds $GatewayReadyTimeoutSeconds
if (-not $GatewayReadiness.ready) {
    $DiagnosticPath = Write-OpenClawGatewayDiagnostic -OpenClaw $OpenClaw `
        -PlatformRoot $PlatformRoot -Readiness $GatewayReadiness
    Write-Host "GATEWAY_FAILURE_CLASS=$($GatewayReadiness.failure_class)"
    Write-Host "GATEWAY_DIAGNOSTIC=$DiagnosticPath"
    throw "Gateway OpenClaw indisponible avant E2E. Classification=$($GatewayReadiness.failure_class). Diagnostic=$DiagnosticPath"
}

$Evidence = [ordered]@{
    schema_version = '1.3.0'
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    platform_root = $PlatformRoot
    backend = $Backend
    expected_provider = $ExpectedProviderLabel
    primary_model = $PrimaryModel
    primary_model_ref = $ModelRef
    openclaw_version = $ActualOpenClawVersion
    cloud_enabled = $false
    transport = 'gateway'
    tool_agent = $ToolAgentId
    tool_workspace = $ToolWorkspace
    scratch_root = $ScratchRoot
    session_prefix = $SessionPrefix
    agent_smoke = @()
    provider_by_agent = [ordered]@{}
    tool_call = $null
    hybrid_vulkan_tool_call = $null
    tool_feedback_repair = $null
    stability = @()
}

$AgentIndex = 0
foreach ($AgentId in $AgentIds) {
    $AgentIndex++
    $AgentModelRef = Get-AgentPrimaryModelRef -Config $Config -AgentId $AgentId
    $ExpectedProvider = Get-ProviderFromModelRef -ModelRef $AgentModelRef
    $Evidence.provider_by_agent[$AgentId] = $ExpectedProvider
    $Prompt = "Réponds en une ligne avec exactement: AGENT_OK $AgentId"
    Write-Host "E2E  Agent $AgentIndex/$($AgentIds.Count): $AgentId -> $ExpectedProvider"
    $Result = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
        'agent', '--agent', $AgentId,
        '--session-key', "$SessionPrefix-smoke-$AgentId",
        '--message', $Prompt,
        '--timeout', [string]$TimeoutSeconds, '--json'
    ) -Description "Smoke agent $AgentId"
    $null = Test-ExpectedProvider -Payload $Result -ExpectedProvider $ExpectedProvider `
        -Description "Smoke agent $AgentId"
    $null = Test-GatewayTransport -Payload $Result -Description "Smoke agent $AgentId"
    $Evidence.agent_smoke += [ordered]@{
        agent = $AgentId
        model_ref = $AgentModelRef
        expected_provider = $ExpectedProvider
        result = $Result
    }
}

$ToolMarkerRelative = "$ScratchPromptPath/tool-call-ok.txt"
$ToolPrompt = @"
Utilise réellement l'outil d'écriture disponible. Dans ton workspace, crée
$ToolMarkerRelative avec exactement TOOL_OK. Ensuite réponds TOOL_OK.
"@
$ToolProvider = Get-ProviderFromModelRef -ModelRef $ModelRef
$ToolResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'agent', '--agent', $ToolAgentId,
    '--session-key', "$SessionPrefix-tool",
    '--model', $ModelRef, '--message', $ToolPrompt,
    '--timeout', [string]$TimeoutSeconds, '--json'
) -Description "Tool-calling OpenClaw/$ToolProvider"
$null = Test-ExpectedProvider -Payload $ToolResult -ExpectedProvider $ToolProvider `
    -Description "Tool-calling OpenClaw/$ToolProvider"
$null = Test-GatewayTransport -Payload $ToolResult `
    -Description "Tool-calling OpenClaw/$ToolProvider"
$ToolMarker = Join-Path $ScratchRoot 'tool-call-ok.txt'
if (-not (Test-Path -LiteralPath $ToolMarker)) {
    throw "Le modèle n'a pas créé le marqueur tool-call-ok.txt."
}
if ((Get-Content -Raw -LiteralPath $ToolMarker).Trim() -ne 'TOOL_OK') {
    throw 'Le contenu du marqueur tool-call-ok.txt est incorrect.'
}
$Evidence.tool_call = $ToolResult

if ($Backend -eq 'b580-hybrid') {
    $VulkanToolRef = 'intel-vulkan/devstral-small-2:24B'
    $VulkanMarkerRelative = "$ScratchPromptPath/vulkan-tool-ok.txt"
    $VulkanMarker = Join-Path $ScratchRoot 'vulkan-tool-ok.txt'
    $VulkanPrompt = @"
Utilise réellement l'outil d'écriture disponible. Dans ton workspace, crée
$VulkanMarkerRelative avec exactement VULKAN_TOOL_OK. Ensuite réponds VULKAN_TOOL_OK.
"@
    $VulkanResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
        'agent', '--agent', $ToolAgentId,
        '--session-key', "$SessionPrefix-vulkan",
        '--model', $VulkanToolRef, '--message', $VulkanPrompt,
        '--timeout', [string]$TimeoutSeconds, '--json'
    ) -Description 'Tool-calling OpenClaw/intel-vulkan'
    $null = Test-ExpectedProvider -Payload $VulkanResult -ExpectedProvider 'intel-vulkan' `
        -Description 'Tool-calling OpenClaw/intel-vulkan'
    $null = Test-GatewayTransport -Payload $VulkanResult `
        -Description 'Tool-calling OpenClaw/intel-vulkan'
    if (-not (Test-Path -LiteralPath $VulkanMarker)) {
        throw 'Devstral/Vulkan n''a pas créé vulkan-tool-ok.txt.'
    }
    if ((Get-Content -Raw -LiteralPath $VulkanMarker).Trim() -ne 'VULKAN_TOOL_OK') {
        throw 'Le contenu de vulkan-tool-ok.txt est incorrect.'
    }
    $Evidence.hybrid_vulkan_tool_call = $VulkanResult
}

$FallbackMarker = Join-Path $ScratchRoot 'fallback.txt'
Set-Content -LiteralPath $FallbackMarker -Value 'FALLBACK_OK' -Encoding utf8
$MissingRelative = "$ScratchPromptPath/missing-intentional.txt"
$FallbackRelative = "$ScratchPromptPath/fallback.txt"
$RepairRelative = "$ScratchPromptPath/repair-ok.txt"
$RepairPrompt = @"
Teste d'abord $MissingRelative, qui n'existe pas. Après l'erreur outil, corrige
le plan: lis $FallbackRelative, puis crée $RepairRelative avec exactement REPAIRED.
Ne fabrique pas le premier résultat.
"@
$RepairResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
    'agent', '--agent', $ToolAgentId,
    '--session-key', "$SessionPrefix-repair",
    '--model', $ModelRef, '--message', $RepairPrompt,
    '--timeout', [string]$TimeoutSeconds, '--json'
) -Description 'Réparation après erreur outil'
$null = Test-ExpectedProvider -Payload $RepairResult -ExpectedProvider $ToolProvider `
    -Description 'Réparation après erreur outil'
$null = Test-GatewayTransport -Payload $RepairResult `
    -Description 'Réparation après erreur outil'
$RepairMarker = Join-Path $ScratchRoot 'repair-ok.txt'
if (-not (Test-Path -LiteralPath $RepairMarker)) {
    throw "Le scénario de réparation n'a pas créé repair-ok.txt."
}
if ((Get-Content -Raw -LiteralPath $RepairMarker).Trim() -ne 'REPAIRED') {
    throw 'Le contenu de repair-ok.txt est incorrect.'
}
$Evidence.tool_feedback_repair = $RepairResult

for ($Run = 1; $Run -le 3; $Run++) {
    $StableResult = Invoke-OpenClawJson -OpenClaw $OpenClaw -Arguments @(
        'agent', '--agent', $ToolAgentId,
        '--session-key', "$SessionPrefix-stable-$Run",
        '--model', $ModelRef, '--message', "Réponds exactement STABLE_$Run",
        '--timeout', [string]$TimeoutSeconds, '--json'
    ) -Description "Stabilité run $Run/3"
    $null = Test-ExpectedProvider -Payload $StableResult -ExpectedProvider $ToolProvider `
        -Description "Stabilité run $Run"
    $null = Test-GatewayTransport -Payload $StableResult -Description "Stabilité run $Run"
    $StableText = Get-OpenClawText -Payload $StableResult
    if ($StableText -notmatch "STABLE_$Run") {
        throw "Stabilité run ${Run}: réponse finale inattendue: $StableText"
    }
    $Evidence.stability += $StableResult
}

New-Item -ItemType Directory -Path $ProofsRoot -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$SafeBackend = $Backend -replace '[^a-zA-Z0-9._-]', '_'
$ProofPath = Join-Path $ProofsRoot "openclaw_e2e_${SafeBackend}_$Stamp.json"
$Evidence | ConvertTo-Json -Depth 50 |
    Set-Content -LiteralPath $ProofPath -Encoding utf8
Write-Host "OK  E2E OpenClaw backend=$Backend terminé: $ProofPath"
Write-Host 'Aucune promotion automatique: revue humaine et qualification matérielle restent requises.'
exit 0
