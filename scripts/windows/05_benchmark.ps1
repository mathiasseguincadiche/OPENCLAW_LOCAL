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
    Write-Host '[DRY-RUN] Chaque scénario borne sa sortie avec max_output_tokens.'
    Write-Host '[DRY-RUN] Le runner affiche durée, TTFT, tokens/s, tokens générés et progression.'
    if ($Quick) {
        Write-Host '[DRY-RUN] Mode QUICK: contexte 8192 uniquement, soit 36 cas avec devops-v2.'
    }
    else {
        Write-Host '[DRY-RUN] Mode COMPLET: contextes 8192 + 16384, soit 72 cas avec devops-v2.'
    }
    exit 0
}

& python @BenchmarkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
