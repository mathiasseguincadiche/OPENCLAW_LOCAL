[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateRange(10, 600)]
    [int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\intel_sycl_smoke.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host '[DRY-RUN] Vérifier sans installer: runtime verrouillé, B580 via SYCL/Level Zero, API 8080 et les trois modèles.'
    Write-Host "[DRY-RUN] Release=$($RuntimeLock.release) Device=$($RuntimeLock.device) Selector=$($RuntimeLock.oneapi_device_selector)"
    Write-Host '[DRY-RUN] Utiliser le runtime Python géré OPENCLAW_LOCAL.'
    Write-Host '[DRY-RUN] Résoudre les IDs réellement annoncés par llama.cpp sans supposer leur casse.'
    Write-Host '[DRY-RUN] Désactiver le thinking uniquement pour le smoke déterministe LOCAL_OK.'
    Write-Host '[DRY-RUN] Vérifier aussi pilote Intel, manifeste/hash du binaire et processus suivi.'
    Write-Host '[DRY-RUN] Produire une preuve locale sans promouvoir le backend.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

$Binary = Get-IntelSyclServerBinary -VersionRoot $Paths.VersionRoot
if (-not $Binary) {
    throw 'Runtime Intel SYCL absent. Exécutez .\menu.ps1 -Action intel-sycl-setup.'
}
if (-not (Test-Path -LiteralPath $Paths.Manifest)) {
    throw 'Manifeste d''intégrité Intel SYCL absent. Relancez intel-sycl-setup.'
}
$Manifest = Get-Content -Raw -LiteralPath $Paths.Manifest | ConvertFrom-Json
$ServerHash = (
    Get-FileHash -LiteralPath $Binary -Algorithm SHA256
).Hash.ToLowerInvariant()
if ($ServerHash -ne ([string]$Manifest.server_sha256).ToLowerInvariant()) {
    throw 'SHA-256 llama-server.exe différent du manifeste. Relancez intel-sycl-setup.'
}
if (([string]$Manifest.archive_sha256).ToLowerInvariant() -ne ([string]$RuntimeLock.sha256).ToLowerInvariant()) {
    throw 'Le manifeste Intel SYCL ne correspond plus au SHA-256 d''archive verrouillé.'
}

$VersionText = (@(& $Binary --version 2>&1) -join "`n").Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Impossible de lire la version llama.cpp SYCL (code $LASTEXITCODE)."
}
$Driver = Get-IntelArcB580DriverInfo
$DeviceText = Test-IntelArcB580SyclDevice -ServerBinary $Binary -RuntimeLock $RuntimeLock

if (-not (Test-Path -LiteralPath $Paths.ProcessState)) {
    throw 'Serveur Intel SYCL non suivi. Exécutez .\menu.ps1 -Action intel-sycl-setup.'
}
$State = Get-Content -Raw -LiteralPath $Paths.ProcessState | ConvertFrom-Json
$Process = Get-Process -Id ([int]$State.pid) -ErrorAction SilentlyContinue
if (-not $Process) {
    throw "État Intel SYCL présent mais processus PID=$($State.pid) absent. Relancez intel-sycl-setup."
}

$Api = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 30
$Advertised = @($Api.data | ForEach-Object { [string]$_.id })
$Expected = Get-RequiredOllamaModelList -RepoRoot $RepoRoot
$Resolved = @()
foreach ($Model in $Expected) {
    $ModelMatches = @($Advertised | Where-Object { $_ -ieq $Model })
    if ($ModelMatches.Count -ne 1) {
        throw (
            "Modèle requis non résolu par le routeur Intel SYCL: $Model. " +
            "Annoncés=$($Advertised -join ', ')"
        )
    }
    $Resolved += [string]$ModelMatches[0]
}

$Smoke = @()
foreach ($Model in $Resolved) {
    $Result = Invoke-IntelSyclDeterministicSmoke -BaseUrl ([string]$RuntimeLock.endpoint) `
        -Model $Model -TimeoutSeconds $TimeoutSeconds
    $Smoke += $Result
    Write-Host "OK  ${Model}: wall=$($Result.wall_ms)ms tok/s=$($Result.tokens_per_second)"
}

$Proof = [ordered]@{
    schema_version = '1.2.0'
    verified_at = [DateTimeOffset]::UtcNow.ToString('o')
    release = [string]$RuntimeLock.release
    expected_archive_sha256 = [string]$RuntimeLock.sha256
    server_sha256 = $ServerHash
    runtime_manifest = $Paths.Manifest
    binary = $Binary
    python = $ManagedPython
    version = $VersionText
    pid = $Process.Id
    endpoint = [string]$RuntimeLock.endpoint
    device = [string]$RuntimeLock.device
    oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
    driver = $Driver
    b580_sycl_evidence = $DeviceText
    ollama_models = @($Expected)
    models = @($Resolved)
    smoke = @($Smoke)
    openclaw_promoted = $false
}
New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$ProofPath = Join-Path $Paths.ProofRoot "verify_${Stamp}.json"
$Proof | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $ProofPath -Encoding utf8
Write-Host "INTEL_SYCL_VERIFY_PROOF=$ProofPath"
Write-Host 'OK  Intel Arc B580 + SYCL/Level Zero + trois modèles vérifiés. Promotion OpenClaw toujours interdite automatiquement.'
exit 0
