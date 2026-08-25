[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [switch]$IncludeSpecialist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Audit = Join-Path $PSScriptRoot '01_audit_host.ps1'
$Verify = Join-Path $PSScriptRoot '04_verify_local.ps1'
$Inventory = Join-Path $PSScriptRoot '06_collect_inventory.ps1'
$Benchmark = Join-Path $RepoRoot 'scripts\benchmark_local.py'
$Evaluate = Join-Path $RepoRoot 'scripts\23_evaluate_benchmark.py'

function Assert-ExitCode([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step en échec (code $LASTEXITCODE)."
    }
}

if ($DryRun) {
    Write-Host '[DRY-RUN] Qualification locale stricte, sans appel cloud :'
    Write-Host '  1. audit host'
    Write-Host '  2. smoke tests Qwen et Gemma'
    Write-Host '  3. inventaire matériel/runtime'
    Write-Host '  4. suite DevOps via API native Ollama'
    Write-Host '  5. évaluation des seuils; aucune promotion automatique'
    if ($Quick) { Write-Host '  mode QUICK: contexte 8192 uniquement' }
    if ($IncludeSpecialist) { Write-Host '  inclure SERA si déjà importé localement' }
    exit 0
}

& $Audit
Assert-ExitCode 'Audit host'

foreach ($Model in @('qwen3.5:9b', 'gemma4')) {
    & $Verify -Model $Model
    Assert-ExitCode "Smoke test $Model"
}

& $Inventory
Assert-ExitCode 'Inventaire'

$BenchmarkArgs = @($Benchmark, '--context', '8192')
if (-not $Quick) {
    $BenchmarkArgs += @('--context', '16384')
}
if ($IncludeSpecialist) {
    $BenchmarkArgs += '--include-specialist'
}
& python @BenchmarkArgs
Assert-ExitCode 'Benchmark local'

& python $Evaluate
Assert-ExitCode 'Évaluation automatique'

Write-Host 'VERDICT: GATE AUTOMATIQUE PASSÉ; QUALIFICATION MANUELLE OPENCLAW ENCORE REQUISE.'
exit 0
