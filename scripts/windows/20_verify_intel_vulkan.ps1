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
    Write-Host '[DRY-RUN] Vérifier le routeur Intel Vulkan suivi sur la B580.'
    Write-Host '[DRY-RUN] Exiger identité du llama-server suivi, Gemma + Devstral, smoke et unload explicite.'
    Write-Host '[DRY-RUN] Ne modifier ni OpenClaw ni le backend nominal.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
if (-not (Test-Path -LiteralPath $Paths.ProcessState)) {
    throw 'État du routeur Intel Vulkan absent. Exécutez intel-vulkan-setup.'
}
$State = Get-Content -Raw -LiteralPath $Paths.ProcessState | ConvertFrom-Json
$Process = Get-Process -Id ([int]$State.pid) -ErrorAction SilentlyContinue
if (-not $Process) {
    throw "Processus Intel Vulkan suivi absent (PID=$($State.pid)). Exécutez intel-vulkan-setup."
}
$ExpectedBinary = Get-IntelVulkanServerBinary -VersionRoot $Paths.VersionRoot
if (-not $ExpectedBinary) {
    throw 'Runtime llama.cpp Vulkan géré absent. Exécutez intel-vulkan-setup.'
}
$ActualProcessPath = try { [string]$Process.Path } catch { '' }
if (-not $ActualProcessPath -or
    -not [string]::Equals(
        [IO.Path]::GetFullPath($ActualProcessPath),
        [IO.Path]::GetFullPath($ExpectedBinary),
        [StringComparison]::OrdinalIgnoreCase
    )) {
    throw (
        "État Intel Vulkan périmé: PID=$($State.pid) ne correspond plus au llama-server géré. " +
        'Exécutez intel-vulkan-setup pour recréer un état propre.'
    )
}
$Inventory = Wait-IntelVulkanApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 30
$Models = Get-IntelVulkanManagedModel -RuntimeLock $RuntimeLock
foreach ($Model in $Models) {
    $null = Resolve-IntelVulkanRuntimeModelId -Inventory $Inventory -LogicalModel $Model
}

$Proof = [ordered]@{
    schema_version = '1.0.0'
    verified_at = [DateTimeOffset]::UtcNow.ToString('o')
    backend = 'llama-cpp-vulkan'
    endpoint = [string]$RuntimeLock.endpoint
    pid = [int]$State.pid
    models = @($Models)
    smoke = @()
    promotion_allowed = $false
}
foreach ($Model in $Models) {
    $Smoke = Invoke-IntelVulkanChatSmoke -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Model
    $Proof.smoke += $Smoke
    Invoke-IntelVulkanModelUnload -BaseUrl ([string]$RuntimeLock.endpoint) -Model $Smoke.runtime_model
    Write-Host "OK  $($Smoke.runtime_model): wall=$($Smoke.wall_ms)ms tok/s=$($Smoke.tokens_per_second)"
}

New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$ProofPath = Join-Path $Paths.ProofRoot "verify_$Stamp.json"
$Proof | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ProofPath -Encoding utf8
Write-Host "INTEL_VULKAN_VERIFY_PROOF=$ProofPath"
Write-Host 'OK  Intel Arc B580 + llama.cpp/Vulkan + Gemma/Devstral vérifiés. Aucune promotion automatique.'
exit 0
