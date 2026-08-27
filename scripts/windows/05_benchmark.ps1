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

$Args = @($Benchmark)
if ($Quick) {
    $Args += @('--context', '8192')
}
if ($IncludeDeep) {
    $Args += '--include-deep'
}
if ($IncludeSpecialist) {
    $Args += '--include-specialist'
}

if ($DryRun) {
    Write-Host "[DRY-RUN] python $($Args -join ' ')"
    Write-Host '[DRY-RUN] La suite est lue depuis qualification_policy.yaml.'
    exit 0
}

& python @Args
if ($LASTEXITCODE -ne 0) {
    throw "Benchmark local en échec (code $LASTEXITCODE)."
}
