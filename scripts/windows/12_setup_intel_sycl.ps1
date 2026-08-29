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

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPaths -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host '[DRY-RUN] Installer et démarrer le backend Intel Arc B580 SYCL/Level Zero.'
    Write-Host "Release     : $($RuntimeLock.release)"
    Write-Host "Asset       : $($RuntimeLock.asset)"
    Write-Host "SHA-256     : $($RuntimeLock.sha256)"
    Write-Host "Device      : $($RuntimeLock.device) via $($RuntimeLock.oneapi_device_selector)"
    Write-Host "Endpoint    : $($RuntimeLock.endpoint)"
    Write-Host "Models max  : $($RuntimeLock.models_max) (un gros modèle à la fois)"
    Write-Host '[DRY-RUN] Réutiliser les blobs GGUF déjà présents dans Ollama; aucun modèle ne sera retéléchargé.'
    Write-Host '[DRY-RUN] Le runtime binaire embarque les dépendances SYCL; pas d''installation oneAPI complète.'
    Write-Host '[DRY-RUN] Aucune promotion OpenClaw automatique; Ollama/Vulkan reste le rollback.'
    exit 0
}

$Proof = [ordered]@{
    schema_version = '1.0.0'
    started_at = [DateTimeOffset]::UtcNow.ToString('o')
    release = [string]$RuntimeLock.release
    asset = [string]$RuntimeLock.asset
    sha256 = [string]$RuntimeLock.sha256
    endpoint = [string]$RuntimeLock.endpoint
    device = [string]$RuntimeLock.device
    oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
    models_max = [int]$RuntimeLock.models_max
    smoke = @()
    status = 'running'
}

try {
    $Binary = Install-IntelSyclRuntime -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot
    $Proof.binary = $Binary
    $Server = Start-IntelSyclServer -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot `
        -TimeoutSeconds $ReadyTimeoutSeconds
    $Proof.pid = $Server.Process.Id
    $Proof.models = @($Server.Models)

    $Smoke = @()
    foreach ($Model in $Server.Models) {
        Write-Host "SMOKE Intel SYCL: $Model"
        $Result = Invoke-IntelSyclChatSmoke -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Model
        $Smoke += $Result
        Write-Host (
            "OK  $Model via SYCL: wall=$($Result.wall_ms)ms " +
            "tok/s=$($Result.tokens_per_second) prompt_tok/s=$($Result.prompt_tokens_per_second)"
        )
    }
    $Proof.smoke = @($Smoke)
    $Proof.status = 'ready'
    $Proof.finished_at = [DateTimeOffset]::UtcNow.ToString('o')

    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $ProofPath = Join-Path $Paths.ProofRoot "setup_${Stamp}.json"
    $Proof | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ProofPath -Encoding utf8
    Write-Host "INTEL_SYCL_PROOF=$ProofPath"
    Write-Host 'OK  Backend Intel SYCL prêt. OpenClaw n''a pas été basculé automatiquement.'
    Write-Host 'Étape suivante: .\menu.ps1 -Action intel-sycl-verify puis intel-sycl-compare.'
    exit 0
}
catch {
    Stop-IntelSyclServer -StatePath $Paths.ProcessState
    $Proof.status = 'failed'
    $Proof.error = $_.Exception.Message
    $Proof.finished_at = [DateTimeOffset]::UtcNow.ToString('o')
    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $FailurePath = Join-Path $Paths.ProofRoot "setup_failed_${Stamp}.json"
    $Proof | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $FailurePath -Encoding utf8
    Write-Host "INTEL_SYCL_PROOF=$FailurePath"
    throw
}
