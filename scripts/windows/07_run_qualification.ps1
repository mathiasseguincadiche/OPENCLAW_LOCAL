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
$Audit = Join-Path $PSScriptRoot '01_audit_host.ps1'
$Verify = Join-Path $PSScriptRoot '04_verify_local.ps1'
$Inventory = Join-Path $PSScriptRoot '06_collect_inventory.ps1'
$Benchmark = Join-Path $PSScriptRoot '05_benchmark.ps1'
$Evaluate = Join-Path $RepoRoot 'scripts\23_evaluate_benchmark.py'
$ListModels = Join-Path $RepoRoot 'scripts\20_list_models.py'

function Assert-ExitCode([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step en échec (code $LASTEXITCODE)."
    }
}

if ($DryRun) {
    Write-Host '[DRY-RUN] Qualification locale stricte, sans appel cloud :'
    Write-Host '  1. audit host'
    Write-Host '  2. smoke tests des modèles required du catalogue'
    Write-Host '  3. inventaire matériel/runtime'
    Write-Host '  4. suite définie dans qualification_policy.yaml'
    Write-Host '  5. évaluation des seuils; aucune promotion automatique'
    if ($Quick) { Write-Host '  mode QUICK: contexte 8192 uniquement' }
    if ($IncludeDeep) { Write-Host '  inclure LOCAL_DEEP Ollama si installé' }
    if ($IncludeSpecialist) {
        Write-Host '  inclure le spécialiste seulement si son provider est qualifié'
    }
    exit 0
}

& $Audit
Assert-ExitCode 'Audit host'

$Models = @(
    & python $ListModels --provider ollama --required
)
Assert-ExitCode 'Lecture du catalogue modèles'
$Models = @($Models | Where-Object { $_ -and $_.Trim() })
if ($Models.Count -eq 0) {
    throw 'Aucun modèle required Ollama dans model_catalog.yaml.'
}

foreach ($Model in $Models) {
    & $Verify -Model $Model
    Assert-ExitCode "Smoke test $Model"
}

& $Inventory
Assert-ExitCode 'Inventaire'

$BenchmarkParameters = @{
    Quick = $Quick
    IncludeDeep = $IncludeDeep
    IncludeSpecialist = $IncludeSpecialist
}
& $Benchmark @BenchmarkParameters
Assert-ExitCode 'Benchmark local'

& python $Evaluate
Assert-ExitCode 'Évaluation automatique'

Write-Host 'VERDICT: GATE AUTOMATIQUE PASSÉ; QUALIFICATION MANUELLE ENCORE REQUISE.'
exit 0
