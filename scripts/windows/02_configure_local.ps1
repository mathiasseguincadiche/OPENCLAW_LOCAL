[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
$ModelsRoot = Join-Path $PlatformRoot 'models\ollama'
$PreviousModelsRoot = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User')
$StorageChanged = $PreviousModelsRoot -ne $ModelsRoot

if ($DryRun) {
    Write-Host "[DRY-RUN] OPENCLAW_LOCAL_ROOT=$PlatformRoot"
    Write-Host "[DRY-RUN] OLLAMA_MODELS=$ModelsRoot"
    Write-Host '[DRY-RUN] OLLAMA_API_KEY=ollama-local'
    if ($StorageChanged) {
        Write-Host '[DRY-RUN] Un serveur Ollama existant serait redémarré pour appliquer le nouvel emplacement.'
    }
    Write-Host '[DRY-RUN] Vérifier ensuite http://127.0.0.1:11434/api/tags.'
    exit 0
}

if ($null -eq (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Ollama est absent. Exécutez d''abord install-core ou install-full.'
}

New-Item -ItemType Directory -Path $ModelsRoot -Force | Out-Null
[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $ModelsRoot, 'User')
[Environment]::SetEnvironmentVariable('OLLAMA_API_KEY', 'ollama-local', 'User')
$env:OLLAMA_MODELS = $ModelsRoot
$env:OLLAMA_API_KEY = 'ollama-local'

$ServerResponding = $false
try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    $ServerResponding = $true
} catch {
    $ServerResponding = $false
}

if ($ServerResponding -and -not $StorageChanged) {
    Write-Host 'OK  Ollama répond déjà sur 127.0.0.1:11434.'
    Write-Host "OK  Modèles Ollama : $ModelsRoot"
    exit 0
}

if ($ServerResponding -and $StorageChanged) {
    Write-Host 'Emplacement des modèles modifié. Redémarrage d''Ollama pour appliquer OLLAMA_MODELS...'
    Get-Process -Name 'ollama' -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
}
else {
    Write-Host 'Ollama ne répond pas encore. Tentative de démarrage local...'
}

Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
for ($Attempt = 1; $Attempt -le 10; $Attempt++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
        Write-Host 'OK  Ollama répond sur 127.0.0.1:11434.'
        Write-Host "OK  Modèles Ollama : $ModelsRoot"
        exit 0
    } catch {
        if ($Attempt -eq 10) {
            throw 'Ollama n''a pas répondu après 10 secondes.'
        }
    }
}
