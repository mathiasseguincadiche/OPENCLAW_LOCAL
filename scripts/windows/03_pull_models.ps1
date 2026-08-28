[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$IncludeOptionalOllama
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Helper = Join-Path $RepoRoot 'scripts\20_list_models.py'

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

if ($IncludeOptionalOllama) {
    throw 'Aucun modèle Ollama optionnel n''est supporté : la flotte locale contient exactement trois modèles required.'
}

$PlatformRoot = Get-PlatformRoot
$ExpectedModelsRoot = Join-Path $PlatformRoot 'models\ollama'

if ($DryRun) {
    Write-Host "[DRY-RUN] OLLAMA_MODELS=$ExpectedModelsRoot"
    Write-Host '[DRY-RUN] Lire les trois modèles required depuis config\v1\model_catalog.yaml.'
    Write-Host '[DRY-RUN] Exécuter un ollama pull pour chacun, sans modèle optionnel.'
    exit 0
}

if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Commande ollama introuvable.'
}
if ($null -eq (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Commande python introuvable.'
}

if ($env:OLLAMA_MODELS -ne $ExpectedModelsRoot) {
    throw "OLLAMA_MODELS doit valoir '$ExpectedModelsRoot'. Exécutez d'abord .\menu.ps1 -Action configure-local."
}
if (-not (Test-Path -LiteralPath $ExpectedModelsRoot)) {
    throw "Répertoire de modèles absent: $ExpectedModelsRoot. Exécutez d'abord configure-local."
}

$Models = @(& python $Helper --provider ollama --required)
if ($LASTEXITCODE -ne 0) {
    throw 'Impossible de lire model_catalog.yaml.'
}
$Models = @($Models | Where-Object { $_ -and $_.Trim() })
if ($Models.Count -ne 3) {
    throw "La flotte locale doit contenir exactement trois modèles required; détectés: $($Models.Count)."
}

foreach ($Model in $Models) {
    Write-Host "Téléchargement/vérification : $Model"
    & ollama pull $Model
    if ($LASTEXITCODE -ne 0) {
        throw "Échec du téléchargement de $Model (code $LASTEXITCODE)."
    }
}
