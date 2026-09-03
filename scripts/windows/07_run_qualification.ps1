[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick
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
$ModelIdentity = Join-Path $RepoRoot 'scripts\48_model_identity_lock.py'
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$QualificationMaxWallSeconds = 2400
$EvaluationReserveSeconds = 60

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Assert-ExitCode([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step en échec (code $LASTEXITCODE)."
    }
}

function Assert-QualificationBudget([System.Diagnostics.Stopwatch]$Watch, [string]$Step) {
    if ($Watch.Elapsed.TotalSeconds -ge $QualificationMaxWallSeconds) {
        throw "HARD_TIMEOUT qualification > 40 min pendant/après $Step."
    }
}

if ($DryRun) {
    Write-Host '[DRY-RUN] Qualification locale stricte, sans appel cloud :'
    Write-Host '  runtime Python: environnement géré OPENCLAW_LOCAL avec PyYAML vérifié'
    Write-Host '  1. audit host + VRAM fiable'
    if ($Quick) {
        Write-Host '  2. smoke tests API des trois modèles required'
    }
    else {
        Write-Host '  2. préflight catalogue uniquement; les smokes redondants sont couverts par le benchmark réel'
    }
    Write-Host '  3. inventaire matériel/runtime'
    Write-Host '  4. capture de l’identité exacte runtime: digest + format + paramètres + quantification'
    Write-Host '  5. benchmark borné des trois modèles selon qualification_policy.yaml'
    Write-Host '  6. progression avec durée, premier token, tokens/s et estimation du restant'
    if ($Quick) {
        Write-Host '  7. diagnostic automatique 8K uniquement; aucune qualification/promotion'
        Write-Host '  mode QUICK: contexte 8192, 36 cas, thinking Qwen désactivé'
        Write-Host '  l’identité modèle n’est jamais promue par un diagnostic QUICK'
    }
    else {
        Write-Host '  7. évaluation complète puis promotion de l’identité uniquement si tout est PASS'
        Write-Host '  mode COMPLET HARD-40M: 24 cas 8K + 6 cas 16K = 30 cas'
        Write-Host '  8 scénarios 8K par modèle; couverture collective des 12 scénarios'
        Write-Host '  2 scénarios 16K ciblés par modèle'
        Write-Host '  Qwen thinking natif uniquement sur 3 probes dédiés'
        Write-Host '  HARD LIMIT qualification complète: 2400 s, évaluation finale incluse'
    }
    exit 0
}

$QualificationWatch = [System.Diagnostics.Stopwatch]::StartNew()
$PlatformRoot = Get-PlatformRoot
$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

& $Audit
Assert-ExitCode 'Audit host'
if (-not $Quick) { Assert-QualificationBudget $QualificationWatch 'audit host' }

$Models = @(
    & $ManagedPython $ListModels --provider ollama --required
)
Assert-ExitCode 'Lecture du catalogue modèles'
$Models = @($Models | Where-Object { $_ -and $_.Trim() })
if ($Models.Count -ne 3) {
    throw "La flotte supportée doit contenir exactement trois modèles required Ollama; détectés: $($Models.Count)."
}

if ($Quick) {
    foreach ($Model in $Models) {
        & $Verify -Model $Model
        Assert-ExitCode "Smoke test $Model"
    }
}
else {
    Write-Host 'OK  Préflight modèles: 3 modèles required; inférence validée dans la matrice benchmark.'
}

& $Inventory
Assert-ExitCode 'Inventaire'
if (-not $Quick) { Assert-QualificationBudget $QualificationWatch 'inventaire' }

if ($Quick) {
    & $Benchmark -Quick
    Assert-ExitCode 'Benchmark local'
    & $ManagedPython $Evaluate --quick
    Assert-ExitCode 'Évaluation diagnostic rapide 8K'
    Write-Host 'VERDICT: QUICK_DIAGNOSTIC_PASS; PASSE COMPLETE 8K+16K ENCORE REQUISE POUR QUALIFICATION.'
    exit 0
}

& $ManagedPython $ModelIdentity --root $PlatformRoot --action capture
Assert-ExitCode 'Capture identité exacte des modèles'
Assert-QualificationBudget $QualificationWatch 'capture identité modèles'

$ElapsedSeconds = [int][Math]::Ceiling($QualificationWatch.Elapsed.TotalSeconds)
$BenchmarkBudgetSeconds = $QualificationMaxWallSeconds - $ElapsedSeconds - $EvaluationReserveSeconds
if ($BenchmarkBudgetSeconds -le 0) {
    throw 'HARD_TIMEOUT: budget de qualification épuisé avant le benchmark.'
}
Write-Host (
    "QUALIFICATION_BUDGET total={0}s elapsed={1}s benchmark={2}s reserve_eval={3}s" -f 
    $QualificationMaxWallSeconds, $ElapsedSeconds, $BenchmarkBudgetSeconds, $EvaluationReserveSeconds
)

& $Benchmark -MaxWallSeconds $BenchmarkBudgetSeconds
Assert-ExitCode 'Benchmark local HARD-40M'
Assert-QualificationBudget $QualificationWatch 'benchmark'

& $ManagedPython $Evaluate
Assert-ExitCode 'Évaluation automatique complète'
Assert-QualificationBudget $QualificationWatch 'évaluation automatique'

& $ManagedPython $ModelIdentity --root $PlatformRoot --action promote
Assert-ExitCode 'Promotion identité modèles qualifiés'
Assert-QualificationBudget $QualificationWatch 'promotion identité modèles'

Write-Host (
    'VERDICT: GATE AUTOMATIQUE PASSÉ POUR LES TROIS MODÈLES; ' +
    'IDENTITÉ DIGEST/QUANTIFICATION VERROUILLÉE; QUALIFICATION MANUELLE ENCORE REQUISE.'
)
Write-Host ("QUALIFICATION_DURATION={0:N1}s" -f $QualificationWatch.Elapsed.TotalSeconds)
exit 0