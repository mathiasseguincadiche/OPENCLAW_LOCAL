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
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host '[DRY-RUN] Installer et démarrer le backend Intel Arc B580 SYCL/Level Zero.'
    Write-Host "Release     : $($RuntimeLock.release)"
    Write-Host "Asset       : $($RuntimeLock.asset)"
    Write-Host "SHA-256     : $($RuntimeLock.sha256)"
    Write-Host "Device      : $($RuntimeLock.device) via $($RuntimeLock.oneapi_device_selector)"
    Write-Host "Endpoint    : $($RuntimeLock.endpoint)"
    Write-Host "Models max  : $($RuntimeLock.models_max) (un gros modèle à la fois)"
    Write-Host '[DRY-RUN] Utiliser le runtime Python géré OPENCLAW_LOCAL, jamais un Python système ambigu.'
    Write-Host '[DRY-RUN] Vérifier le pilote B580, l''archive officielle, le manifeste du binaire et le port 8080.'
    Write-Host '[DRY-RUN] Résoudre les IDs réellement annoncés par le routeur llama.cpp avant les smokes.'
    Write-Host '[DRY-RUN] Réutiliser les blobs GGUF déjà présents dans Ollama; aucun modèle ne sera retéléchargé.'
    Write-Host '[DRY-RUN] Le runtime binaire embarque les dépendances SYCL; pas d''installation oneAPI complète.'
    Write-Host '[DRY-RUN] Aucune promotion OpenClaw automatique; Ollama/Vulkan reste le rollback.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

$Proof = [ordered]@{
    schema_version = '1.1.0'
    started_at = [DateTimeOffset]::UtcNow.ToString('o')
    release = [string]$RuntimeLock.release
    asset = [string]$RuntimeLock.asset
    archive_sha256 = [string]$RuntimeLock.sha256
    endpoint = [string]$RuntimeLock.endpoint
    device = [string]$RuntimeLock.device
    oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
    models_max = [int]$RuntimeLock.models_max
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
    $Server = Start-IntelSyclServer -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot `
        -TimeoutSeconds $ReadyTimeoutSeconds
    $Proof.pid = $Server.Process.Id
    $Proof.ollama_models = @($Server.Models)
    $Proof.driver = $Server.Driver

    $Api = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 30
    $Advertised = @($Api.data | ForEach-Object { [string]$_.id })
    $ResolvedModels = @()
    foreach ($ExpectedModel in $Server.Models) {
        $Matches = @($Advertised | Where-Object { $_ -ieq [string]$ExpectedModel })
        if ($Matches.Count -ne 1) {
            throw (
                "Impossible de résoudre l'ID llama.cpp pour $ExpectedModel. " +
                "Annoncés=$($Advertised -join ', ')"
            )
        }
        $ResolvedModels += [string]$Matches[0]
    }
    $Proof.models = @($ResolvedModels)

    $Smoke = @()
    foreach ($Model in $ResolvedModels) {
        Write-Host "SMOKE Intel SYCL: $Model"
        $Result = Invoke-IntelSyclChatSmoke `
            -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Model
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
    Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
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
