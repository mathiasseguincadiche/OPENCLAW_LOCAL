[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Benchmark = Join-Path $RepoRoot 'scripts\benchmark_local.py'
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

$BenchmarkArgs = @($Benchmark)
if ($Quick) {
    $BenchmarkArgs += @('--context', '8192', '--qwen-thinking', 'off')
}
else {
    $BenchmarkArgs += @('--qwen-thinking', 'native')
}

if ($DryRun) {
    Write-Host "[DRY-RUN] Python géré OPENCLAW_LOCAL -> $($BenchmarkArgs -join ' ')"
    Write-Host '[DRY-RUN] Les trois modèles requis et la suite sont lus depuis les contrats YAML.'
    Write-Host '[DRY-RUN] Chaque scénario borne sa sortie avec max_output_tokens.'
    Write-Host '[DRY-RUN] Gemma 4: thinking désactivé pour préserver le budget de réponse finale des gates fonctionnels.'
    Write-Host '[DRY-RUN] Le runner affiche durée, premier token, réponse finale, tokens/s et progression.'
    if ($Quick) {
        Write-Host '[DRY-RUN] Mode QUICK: contexte 8192, 36 cas, thinking Qwen désactivé.'
    }
    else {
        Write-Host '[DRY-RUN] Mode COMPLET OPTIMISÉ: 36 cas 8K + 12 cas ciblés 16K = 48 cas.'
        Write-Host '[DRY-RUN] Qwen thinking natif conservé mais borné à 768 tokens par cas.'
        Write-Host '[DRY-RUN] 16K cible intake projet, diagnostic K8s, réparation outil et long contexte.'
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
