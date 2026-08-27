[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Model
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ListModels = Join-Path $RepoRoot 'scripts\20_list_models.py'

if (-not $Model) {
    $RequiredModels = @(
        & python $ListModels --provider ollama --required
    )
    if ($LASTEXITCODE -ne 0) {
        throw 'Impossible de lire model_catalog.yaml.'
    }
    $RequiredModels = @($RequiredModels | Where-Object { $_ -and $_.Trim() })
    if ($RequiredModels.Count -eq 0) {
        throw 'Aucun modèle required Ollama dans model_catalog.yaml.'
    }
    $Model = $RequiredModels[0]
}

if ($DryRun) {
    Write-Host "[DRY-RUN] Vérifier Ollama puis exécuter un smoke test avec $Model."
    exit 0
}

$null = Invoke-RestMethod -Method Get `
    -Uri 'http://127.0.0.1:11434/api/tags' `
    -TimeoutSec 5
$Prompt = 'Réponds uniquement avec le texte LOCAL_OK, sans ponctuation ni explication.'
$Output = (& ollama run $Model $Prompt | Out-String).Trim()

if ($LASTEXITCODE -ne 0) {
    throw "Inférence Ollama en échec (code $LASTEXITCODE)."
}

if ($Output -notmatch 'LOCAL_OK') {
    throw "Smoke test inattendu. Réponse reçue: $Output"
}

Write-Host "OK  Inférence locale validée avec $Model."
