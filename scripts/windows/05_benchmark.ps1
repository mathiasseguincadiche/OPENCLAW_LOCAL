[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [int]$MaxWallSeconds = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$QuickBenchmark = Join-Path $RepoRoot 'scripts\benchmark_local.py'
$FullBenchmark = Join-Path $RepoRoot 'scripts\benchmark_qualification_40m_v2.py'
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

if ($MaxWallSeconds -lt 0) {
    throw 'MaxWallSeconds doit être positif ou nul.'
}

if ($Quick) {
    $BenchmarkArgs = @($QuickBenchmark, '--context', '8192', '--qwen-thinking', 'off')
}
else {
    $BenchmarkArgs = @($FullBenchmark)
    if ($MaxWallSeconds -gt 0) {
        $BenchmarkArgs += @('--max-wall-seconds', [string]$MaxWallSeconds)
    }
}

if ($DryRun) {
    Write-Host "[DRY-RUN] Python géré OPENCLAW_LOCAL -> $($BenchmarkArgs -join ' ')"
    Write-Host '[DRY-RUN] Les trois modèles requis et la suite sont lus depuis les contrats YAML.'
    Write-Host '[DRY-RUN] Chaque scénario borne sa sortie avec max_output_tokens.'
    Write-Host '[DRY-RUN] Le runner affiche durée, premier token, réponse finale, tokens/s et progression.'
    if ($Quick) {
        Write-Host '[DRY-RUN] Mode QUICK: contexte 8192, 36 cas, thinking Qwen désactivé.'
    }
    else {
        Write-Host '[DRY-RUN] Mode COMPLET HARD-40M: 24 cas 8K + 6 cas 16K = 30 cas.'
        Write-Host '[DRY-RUN] Couverture collective des 12 scénarios; 8 scénarios par modèle à 8K.'
        Write-Host '[DRY-RUN] 16K: 2 scénarios ciblés par modèle.'
        Write-Host '[DRY-RUN] Qwen thinking natif uniquement sur 3 probes; plafond 768 tokens.'
        Write-Host '[DRY-RUN] Runner full: budget benchmark par défaut 35 min, timeout par cas 210 s.'
        Write-Host '[DRY-RUN] La limite globale qualification reste 2400 s et reste prioritaire.'
    }
    exit 0
}

$PlatformRoot = Get-PlatformRoot
$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

& $ManagedPython @BenchmarkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
