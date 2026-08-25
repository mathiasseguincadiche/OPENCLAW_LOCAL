[CmdletBinding()]
param(
    [switch]$DryRun,
    [string[]]$Models = @('qwen3.5:9b', 'gemma4')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Commande ollama introuvable.'
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
