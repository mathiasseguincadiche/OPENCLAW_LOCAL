[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$CompareScript = Join-Path $RepoRoot 'scripts\28_compare_local_backends.py'

if ($DryRun) {
    $Mode = if ($Quick) { 'QUICK: 1 scénario, 1 répétition' } else { 'COMPLET: 2 scénarios, 2 répétitions' }
    Write-Host "[DRY-RUN] Comparaison B580 Ollama/Vulkan vs llama.cpp/SYCL — $Mode."
    Write-Host '[DRY-RUN] Mêmes trois modèles, contexte 8192, température 0, Qwen thinking off pour comparabilité.'
    Write-Host '[DRY-RUN] Mesurer durée, chargement, prompt tok/s, decode tok/s et changements de modèle.'
    Write-Host '[DRY-RUN] Le résultat ne peut pas promouvoir automatiquement le backend.'
    exit 0
}

try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
}
catch {
    throw "Ollama/Vulkan n'est pas disponible pour la comparaison: $($_.Exception.Message)"
}
try {
    $null = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 10
}
catch {
    throw 'Intel SYCL n''est pas prêt. Exécutez .\menu.ps1 -Action intel-sycl-setup.'
}

$Arguments = @($CompareScript)
if ($Quick) {
    $Arguments += @('--quick', '--repetitions', '1')
}
else {
    $Arguments += @('--repetitions', '2')
}

& python @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Comparaison Ollama/SYCL en échec (code $LASTEXITCODE)."
}
Write-Host 'OK  Comparaison B580 terminée. Aucun backend n''a été promu automatiquement.'
exit 0
