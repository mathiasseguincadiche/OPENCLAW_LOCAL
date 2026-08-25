[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Model = 'qwen3.5:9b'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($DryRun) {
    Write-Host "[DRY-RUN] Vérifier Ollama puis exécuter un smoke test avec $Model."
    exit 0
}

$null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
$Prompt = 'Réponds uniquement avec le texte LOCAL_OK, sans ponctuation ni explication.'
$Output = (& ollama run $Model $Prompt | Out-String).Trim()

if ($LASTEXITCODE -ne 0) {
    throw "Inférence Ollama en échec (code $LASTEXITCODE)."
}

if ($Output -notmatch 'LOCAL_OK') {
    throw "Smoke test inattendu. Réponse reçue: $Output"
}

Write-Host "OK  Inférence locale validée avec $Model."
