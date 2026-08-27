[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [switch]$IncludeDeep,
    [switch]$IncludeSpecialist,
    [switch]$IncludeMax
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Benchmark = Join-Path $RepoRoot 'scripts\benchmark_local.py'

$BenchmarkArgs = @($Benchmark)
if ($Quick) {
    $BenchmarkArgs += @('--context', '8192')
}
if ($IncludeDeep) {
    $BenchmarkArgs += '--include-deep'
}
if ($IncludeSpecialist) {
    $BenchmarkArgs += '--include-specialist'
}
if ($IncludeMax) {
    $BenchmarkArgs += '--include-max'
}

if ($DryRun) {
    Write-Host "[DRY-RUN] python $($BenchmarkArgs -join ' ')"
    Write-Host '[DRY-RUN] La suite et les classes de modèles sont lues depuis les contrats YAML.'
    exit 0
}

& python @BenchmarkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
