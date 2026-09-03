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
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

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

if ($DryRun) {
    Write-Host '[DRY-RUN] Qualification locale stricte, sans appel cloud :'
    Write-Host '  runtime Python: environnement géré OPENCLAW_LOCAL avec PyYAML vérifié'
    Write-Host '  1. audit host avec VRAM fiable si HardwareInformation.qwMemorySize est disponible'
    Write-Host '  2. smoke tests API sans spinner des trois modèles required du catalogue'
    Write-Host '  3. inventaire matériel/runtime'
    Write-Host '  4. benchmark borné des trois modèles selon qualification_policy.yaml'
    Write-Host '  5. progression avec durée, TTFT, tokens/s et estimation du restant'
    Write-Host '  politique Gemma 4: thinking désactivé dans les gates fonctionnels bornés'
    if ($Quick) {
        Write-Host '  6. diagnostic automatique 8K uniquement; aucune qualification/promotion'
        Write-Host '  mode QUICK: contexte 8192, 36 cas, thinking Qwen désactivé'
    }
    else {
        Write-Host '  6. évaluation complète des seuils; aucune promotion automatique'
        Write-Host '  mode COMPLET: contextes 8192 + 16384, 72 cas, thinking Qwen natif et borné'
    }
    exit 0
}

$PlatformRoot = Get-PlatformRoot
$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

& $Audit
Assert-ExitCode 'Audit host'

$Models = @(
    & $ManagedPython $ListModels --provider ollama --required
)
Assert-ExitCode 'Lecture du catalogue modèles'
$Models = @($Models | Where-Object { $_ -and $_.Trim() })
if ($Models.Count -ne 3) {
    throw "La flotte supportée doit contenir exactement trois modèles required Ollama; détectés: $($Models.Count)."
}

foreach ($Model in $Models) {
    & $Verify -Model $Model
    Assert-ExitCode "Smoke test $Model"
}

& $Inventory
Assert-ExitCode 'Inventaire'

& $Benchmark -Quick:$Quick
Assert-ExitCode 'Benchmark local'

if ($Quick) {
    & $ManagedPython $Evaluate --quick
    Assert-ExitCode 'Évaluation diagnostic rapide 8K'
    Write-Host 'VERDICT: QUICK_DIAGNOSTIC_PASS; PASSE COMPLETE 8K+16K ENCORE REQUISE POUR QUALIFICATION.'
    exit 0
}

& $ManagedPython $Evaluate
Assert-ExitCode 'Évaluation automatique complète'

Write-Host 'VERDICT: GATE AUTOMATIQUE PASSÉ POUR LES TROIS MODÈLES; QUALIFICATION MANUELLE ENCORE REQUISE.'
exit 0
