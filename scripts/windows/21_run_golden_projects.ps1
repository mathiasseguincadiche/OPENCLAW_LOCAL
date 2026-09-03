[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Runner = Join-Path $RepoRoot 'scripts\49_run_golden_projects.py'
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

$PlatformRoot = Get-PlatformRoot

if ($DryRun) {
    Write-Host '[DRY-RUN] Golden projects pré-V1 via Python géré OPENCLAW_LOCAL.'
    Write-Host '[DRY-RUN] 5 scénarios: reset propre -> prepare -> execute -> evaluate.'
    Write-Host '[DRY-RUN] Root projets:' $PlatformRoot
    Write-Host '[DRY-RUN] Aucun fallback cloud implicite; approbation humaine finale inchangée.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
Write-Host 'GOLDEN_PLAN scenarios=5 reset=true prepare=true execute=true evaluate=true'

& $ManagedPython $Runner --root $PlatformRoot --scenario all --prepare --reset --execute --evaluate
if ($LASTEXITCODE -ne 0) {
    throw "Golden projects pré-V1 en échec (code $LASTEXITCODE)."
}

Write-Host 'VERDICT: GOLDEN_PROJECTS_PASS — cinq scénarios préparés, exécutés et évalués.'
exit 0
