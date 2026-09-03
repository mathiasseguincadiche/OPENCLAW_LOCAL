[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\intel_sycl_model_sources.ps1')
. (Join-Path $PSScriptRoot 'lib\intel_sycl_smoke.ps1')
. (Join-Path $PSScriptRoot 'lib\intel_sycl_model_lifecycle.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ([int]$RuntimeLock.parallel -ne 1) {
    throw 'Contrat Intel SYCL invalide: parallel=1 requis pour un seul modèle sur B580.'
}

if ($DryRun) {
    Write-Host '[DRY-RUN] Installer et démarrer le backend Intel Arc B580 SYCL/Level Zero.'
    Write-Host "Release     : $($RuntimeLock.release)"
    Write-Host "Asset       : $($RuntimeLock.asset)"
    Write-Host "SHA-256     : $($RuntimeLock.sha256)"
    Write-Host "Device      : $($RuntimeLock.device) via $($RuntimeLock.oneapi_device_selector)"
    Write-Host "Endpoint    : $($RuntimeLock.endpoint)"
    Write-Host "Models max  : $($RuntimeLock.models_max) (un modèle à la fois)"
    Write-Host "Context     : $($RuntimeLock.context_tokens) tokens nominal B580"
    Write-Host "Parallel    : $($RuntimeLock.parallel) slot (évite le défaut auto=4 de llama-server)"
    Write-Host '[DRY-RUN] Utiliser le runtime Python géré OPENCLAW_LOCAL, jamais un Python système ambigu.'
    Write-Host '[DRY-RUN] Vérifier le pilote B580, l''archive officielle, le manifeste du binaire et le port 8080.'
    Write-Host '[DRY-RUN] Résoudre les IDs réellement annoncés par le routeur llama.cpp avant les smokes.'
    Write-Host '[DRY-RUN] Désactiver le thinking uniquement pour le smoke déterministe LOCAL_OK.'
    Write-Host '[DRY-RUN] Décharger explicitement chaque modèle et attendre unloaded avant le switch suivant.'
    Write-Host '[DRY-RUN] Les trois modèles utilisent le blob GGUF Ollama sauf override natif explicitement verrouillé.'
    Write-Host '[DRY-RUN] Aucun override natif n''est requis par la flotte B580 Q4_K_M actuelle.'
    Write-Host '[DRY-RUN] Le runtime binaire embarque les dépendances SYCL; pas d''installation oneAPI complète.'
    Write-Host '[DRY-RUN] Le stop du processus suivi ne doit jamais contaminer la sortie objet de Start-IntelSyclServer.'
    Write-Host '[DRY-RUN] Aucune promotion OpenClaw automatique; Ollama/Vulkan reste le rollback.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

$Proof = [ordered]@{
    schema_version = '1.6.0'
    started_at = [DateTimeOffset]::UtcNow.ToString('o')
    release = [string]$RuntimeLock.release
    asset = [string]$RuntimeLock.asset
    archive_sha256 = [string]$RuntimeLock.sha256
    endpoint = [string]$RuntimeLock.endpoint
    device = [string]$RuntimeLock.device
    oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
    models_max = [int]$RuntimeLock.models_max
    parallel = [int]$RuntimeLock.parallel
    context_tokens = [int]$RuntimeLock.context_tokens
    model_source_policy = [string]$RuntimeLock.model_source_policy
    explicit_unload_between_models = $true
    strict_process_output_contract = $true
    single_slot_runtime_contract = $true
    python = $ManagedPython
    runtime_manifest = $Paths.Manifest
    smoke = @()
    status = 'running'
}

try {
    $Binary = Install-IntelSyclRuntime -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot
    $Proof.binary = $Binary
    $Proof.server_sha256 = (
        Get-FileHash -LiteralPath $Binary -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    $PreviousParallel = $env:LLAMA_ARG_N_PARALLEL
    try {
        $env:LLAMA_ARG_N_PARALLEL = [string]$RuntimeLock.parallel
        Write-Host "OK  llama-server Intel SYCL forcé à $($RuntimeLock.parallel) slot."
        $Server = Start-IntelSyclServer -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot `
            -TimeoutSeconds $ReadyTimeoutSeconds
    }
    finally {
        if ($null -eq $PreviousParallel) {
            Remove-Item Env:LLAMA_ARG_N_PARALLEL -ErrorAction SilentlyContinue
        }
        else {
            $env:LLAMA_ARG_N_PARALLEL = $PreviousParallel
        }
    }

    if (
        -not $Server -or
        -not $Server.PSObject.Properties['Process'] -or
        $null -eq $Server.Process
    ) {
        throw 'Contrat Start-IntelSyclServer invalide: objet runtime unique attendu avec Process non-null.'
    }
    $Proof.pid = $Server.Process.Id
    $Proof.ollama_models = @($Server.Models)
    $Proof.driver = $Server.Driver

    $Api = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 30
    $Advertised = @($Api.data | ForEach-Object { [string]$_.id })
    $ResolvedModels = @()
    foreach ($ExpectedModel in $Server.Models) {
        $ModelMatches = @($Advertised | Where-Object { $_ -ieq [string]$ExpectedModel })
        if ($ModelMatches.Count -ne 1) {
            throw (
                "Impossible de résoudre l'ID llama.cpp pour $ExpectedModel. " +
                "Annoncés=$($Advertised -join ', ')"
            )
        }
        $ResolvedModels += [string]$ModelMatches[0]
    }
    $Proof.models = @($ResolvedModels)

    $Smoke = @()
    foreach ($Model in $ResolvedModels) {
        Write-Host "SMOKE Intel SYCL: $Model"
        $Result = Invoke-IntelSyclDeterministicSmoke `
            -BaseUrl ([string]$RuntimeLock.endpoint) `
            -Model $Model `
            -DiagnosticLogPath $Paths.StderrLog
        Remove-IntelSyclModel `
            -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Model `
            -TimeoutSeconds 90 -Confirm:$false
        $Result | Add-Member -NotePropertyName unloaded_after_smoke -NotePropertyValue $true
        $Smoke += $Result
        Write-Host (
            "OK  $Model via SYCL: wall=$($Result.wall_ms)ms " +
            "tok/s=$($Result.tokens_per_second) " +
            "prompt_tok/s=$($Result.prompt_tokens_per_second)"
        )
    }
    $Proof.smoke = @($Smoke)
    $Proof.status = 'ready'
    $Proof.finished_at = [DateTimeOffset]::UtcNow.ToString('o')

    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $ProofPath = Join-Path $Paths.ProofRoot "setup_${Stamp}.json"
    $Proof | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath $ProofPath -Encoding utf8
    Write-Host "INTEL_SYCL_PROOF=$ProofPath"
    Write-Host 'OK  Backend Intel SYCL prêt. OpenClaw n''a pas été basculé automatiquement.'
    Write-Host 'Étape suivante: .\menu.ps1 -Action intel-sycl-verify puis intel-sycl-compare.'
    exit 0
}
catch {
    $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
    $Proof.status = 'failed'
    $Proof.error = $_.Exception.Message
    $Proof.finished_at = [DateTimeOffset]::UtcNow.ToString('o')
    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $FailurePath = Join-Path $Paths.ProofRoot "setup_failed_${Stamp}.json"
    $Proof | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath $FailurePath -Encoding utf8
    Write-Host "INTEL_SYCL_PROOF=$FailurePath"
    throw
}