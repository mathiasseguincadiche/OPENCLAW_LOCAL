[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Ollama est absent. Installez la version Windows officielle puis relancez cette action.'
}

if ($DryRun) {
    Write-Host '[DRY-RUN] Définir OLLAMA_API_KEY=ollama-local au niveau utilisateur.'
    Write-Host '[DRY-RUN] Vérifier http://127.0.0.1:11434/api/tags.'
    exit 0
}

[Environment]::SetEnvironmentVariable('OLLAMA_API_KEY', 'ollama-local', 'User')
$env:OLLAMA_API_KEY = 'ollama-local'

try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    Write-Host 'OK  Ollama répond déjà sur 127.0.0.1:11434.'
    exit 0
} catch {
    Write-Host 'Ollama ne répond pas encore. Tentative de démarrage local...'
}

Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
for ($Attempt = 1; $Attempt -le 10; $Attempt++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
        Write-Host 'OK  Ollama répond sur 127.0.0.1:11434.'
        exit 0
    } catch {
        if ($Attempt -eq 10) {
            throw 'Ollama n''a pas répondu après 10 secondes.'
        }
    }
}
