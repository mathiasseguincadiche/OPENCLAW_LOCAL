[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Benchmark = Join-Path $RepoRoot 'scripts\benchmark_local.py'

$BenchmarkArgs = @($Benchmark)
if ($Quick) {
    $BenchmarkArgs += @('--context', '8192')
}

if ($DryRun) {
    Write-Host "[DRY-RUN] python $($BenchmarkArgs -join ' ')"
    Write-Host '[DRY-RUN] Les trois modèles requis et la suite sont lus depuis les contrats YAML.'
    exit 0
}

& python @BenchmarkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
