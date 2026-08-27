[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [switch]$IncludeDeep,
    [switch]$IncludeSpecialist
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

if ($DryRun) {
    Write-Host "[DRY-RUN] python $($BenchmarkArgs -join ' ')"
    Write-Host '[DRY-RUN] La suite est lue depuis qualification_policy.yaml.'
    exit 0
}

& python @BenchmarkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
