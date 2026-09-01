[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_vulkan.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelVulkanRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelVulkanPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host '[DRY-RUN] Installer/vérifier llama.cpp Vulkan b10621 géré.'
    Write-Host "[DRY-RUN] Endpoint=$($RuntimeLock.endpoint) models=$(@($RuntimeLock.managed_models) -join ',')"
    Write-Host '[DRY-RUN] Arrêter le routeur SYCL suivi avant Vulkan pour éviter toute contention B580.'
    Write-Host '[DRY-RUN] Démarrer models_max=1, parallel=1, gpu_layers=auto, fit=on.'
    Write-Host '[DRY-RUN] Smoke Gemma + Devstral puis unload explicite entre modèles.'
    Write-Host '[DRY-RUN] OpenClaw ne sera pas reconfiguré automatiquement.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
$Binary = Install-IntelVulkanRuntime -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot

$SyclLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$SyclPaths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $SyclLock
$null = Stop-IntelSyclServer -StatePath $SyclPaths.ProcessState -Confirm:$false

$Server = $null
$Proof = [ordered]@{
    schema_version = '1.0.0'
    started_at = [DateTimeOffset]::UtcNow.ToString('o')
    backend = 'llama-cpp-vulkan'
    endpoint = [string]$RuntimeLock.endpoint
    binary = $Binary
    release = [string]$RuntimeLock.release
    models_max = [int]$RuntimeLock.models_max
    parallel = [int]$RuntimeLock.parallel
    gpu_layers = [string]$RuntimeLock.gpu_layers
    context_tokens = [int]$RuntimeLock.context_tokens
    smoke = @()
    openclaw_modified = $false
    promotion_allowed = $false
}
try {
    $Server = Start-IntelVulkanServer -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot -Confirm:$false
    if (-not $Server -or -not $Server.Process) {
        throw 'Start-IntelVulkanServer n''a pas retourné un runtime suivi valide.'
    }
    $Proof.pid = $Server.Process.Id
    $Proof.device = [string]$Server.Device.id
    foreach ($Model in $Server.Models) {
        Write-Host "SMOKE Intel Vulkan: $Model"
        $Smoke = Invoke-IntelVulkanChatSmoke -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Model
        $Proof.smoke += $Smoke
        Unload-IntelVulkanModel -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Smoke.runtime_model
        Write-Host "OK  $($Smoke.runtime_model) via Vulkan: wall=$($Smoke.wall_ms)ms tok/s=$($Smoke.tokens_per_second) prompt_tok/s=$($Smoke.prompt_tokens_per_second)"
    }
    $Proof.status = 'pass'
}
catch {
    $Proof.status = 'fail'
    $Proof.error = $_.Exception.Message
    if ($Server) {
        $null = Stop-IntelVulkanServer -StatePath $Paths.ProcessState -Confirm:$false
    }
    throw
}
finally {
    $Proof.finished_at = [DateTimeOffset]::UtcNow.ToString('o')
    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $ProofPath = Join-Path $Paths.ProofRoot "setup_$Stamp.json"
    $Proof | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ProofPath -Encoding utf8
    Write-Host "INTEL_VULKAN_PROOF=$ProofPath"
}

Write-Host 'OK  Backend Intel Vulkan géré prêt. OpenClaw n''a pas été basculé automatiquement.'
Write-Host 'Étape suivante: .\menu.ps1 -Action intel-vulkan-verify puis configure-openclaw -Backend b580-hybrid.'
exit 0
