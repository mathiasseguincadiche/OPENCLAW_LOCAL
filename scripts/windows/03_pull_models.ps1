[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$IncludeOptionalOllama
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Helper = Join-Path $RepoRoot 'scripts\20_list_models.py'

if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Commande ollama introuvable.'
}
if ($null -eq (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Commande python introuvable.'
}

$ListArgs = @($Helper, '--provider', 'ollama')
if (-not $IncludeOptionalOllama) {
    $ListArgs += '--required'
}
$Models = @(& python @ListArgs)
if ($LASTEXITCODE -ne 0) {
    throw 'Impossible de lire model_catalog.yaml.'
}
$Models = @($Models | Where-Object { $_ -and $_.Trim() })
if ($Models.Count -eq 0) {
    throw 'Aucun modèle Ollama sélectionné dans model_catalog.yaml.'
}

foreach ($Model in $Models) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] ollama pull $Model"
        continue
    }

    Write-Host "Téléchargement/vérification : $Model"
    & ollama pull $Model
    if ($LASTEXITCODE -ne 0) {
        throw "Échec du téléchargement de $Model (code $LASTEXITCODE)."
    }
}
