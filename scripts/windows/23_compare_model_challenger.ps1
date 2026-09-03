[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateRange(1, 10)]
    [int]$Repetitions = 3,
    [ValidateRange(2048, 32768)]
    [int]$ContextTokens = 8192,
    [ValidateRange(10, 600)]
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Runner = Join-Path $RepoRoot 'scripts\52_compare_tool_calling_models.py'
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

$RunnerArgs = @(
    $Runner,
    '--repetitions', [string]$Repetitions,
    '--context', [string]$ContextTokens,
    '--timeout', [string]$TimeoutSeconds
)

if ($DryRun) {
    Write-Host '[DRY-RUN] Comparaison obligatoire de sélection du modèle deep.'
    Write-Host '[DRY-RUN] Incumbent : gemma-deep -> gemma3:12b-it-q4_K_M.'
    Write-Host '[DRY-RUN] Challenger: ministral-tool-calling -> ministral-3:14b-instruct-2512-q4_K_M.'
    Write-Host '[DRY-RUN] Protocole: tool-calling natif + réparation après file_not_found.'
    Write-Host "[DRY-RUN] Répétitions=$Repetitions contexte=$ContextTokens timeout=$TimeoutSeconds s."
    Write-Host '[DRY-RUN] Le challenger ne devient jamais un quatrième modèle routé.'
    Write-Host '[DRY-RUN] Aucune promotion automatique; décision humaine obligatoire.'
    Write-Host '[DRY-RUN] Si absent: ollama pull ministral-3:14b-instruct-2512-q4_K_M'
    exit 0
}

if (-not (Test-Path -LiteralPath $Runner)) {
    throw "Runner challenger introuvable: $Runner"
}

$PlatformRoot = Get-PlatformRoot
$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
Write-Host 'INFO Le benchmark ne télécharge aucun modèle implicitement.'

& $ManagedPython @RunnerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Comparaison Gemma/Ministral incomplète (code $LASTEXITCODE)."
}

Write-Host 'OK  Preuve challenger produite. Aucune promotion de modèle effectuée.'
exit 0
