[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateSet('native', 'off')]
    [string]$ThinkingMode = 'native',
    [ValidateRange(1, 3)]
    [int]$Repeats = 1,
    [ValidateRange(1, 2048)]
    [int]$MaxOutputTokens = 1536,
    [ValidateRange(1, 3600)]
    [int]$CaseTimeoutSeconds = 480
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Runner = Join-Path $RepoRoot 'scripts\50_calibrate_qwen_native.py'
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

$Arguments = @(
    $Runner,
    '--thinking-mode', $ThinkingMode,
    '--repeats', [string]$Repeats,
    '--max-output-tokens', [string]$MaxOutputTokens,
    '--case-timeout-seconds', [string]$CaseTimeoutSeconds
)

if ($DryRun) {
    Write-Host '[DRY-RUN] Calibration Qwen thinking non promotionnelle.'
    Write-Host '[DRY-RUN] Les 3 probes viennent de qualification_policy.yaml.'
    Write-Host "[DRY-RUN] thinking=$ThinkingMode repeats=$Repeats max_out=$MaxOutputTokens timeout=${CaseTimeoutSeconds}s"
    Write-Host '[DRY-RUN] native conserve le reasoning Qwen; off envoie think=false.'
    Write-Host '[DRY-RUN] Le runner continue après timeout/troncature pour mesurer les 3 probes.'
    Write-Host "[DRY-RUN] Aucune qualification, identité modèle ou promotion backend n'est modifiée."
    exit 0
}

$PlatformRoot = Get-PlatformRoot
$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"

& $ManagedPython @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Calibration Qwen thinking en échec technique (code $LASTEXITCODE)."
}
