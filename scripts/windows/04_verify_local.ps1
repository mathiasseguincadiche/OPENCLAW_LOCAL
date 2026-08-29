[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Model,
    [ValidateRange(10, 600)]
    [int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ListModels = Join-Path $RepoRoot 'scripts\20_list_models.py'
$OllamaEndpoint = 'http://127.0.0.1:11434'

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
    Write-Host "[DRY-RUN] Vérifier Ollama puis exécuter un smoke test /api/chat sans spinner avec $Model."
    Write-Host '[DRY-RUN] Lire ensuite /api/ps pour exposer la part réellement chargée en VRAM.'
    exit 0
}

try {
    $Tags = Invoke-RestMethod -Method Get `
        -Uri "$OllamaEndpoint/api/tags" `
        -TimeoutSec 5
}
catch {
    throw "API Ollama inaccessible sur loopback: $($_.Exception.Message)"
}

$AvailableModels = @(
    $Tags.models |
        ForEach-Object { [string]$_.name } |
        Where-Object { $_ -and $_.Trim() }
)
if ($AvailableModels -notcontains $Model) {
    throw "Modèle Ollama absent localement: $Model. Aucun téléchargement implicite n'est autorisé."
}

$Prompt = 'Réponds uniquement avec le texte LOCAL_OK, sans ponctuation ni explication.'
$RequestBody = [ordered]@{
    model = $Model
    messages = @(
        [ordered]@{
            role = 'user'
            content = $Prompt
        }
    )
    stream = $false
    keep_alive = '15m'
    options = [ordered]@{
        num_ctx = 2048
        temperature = 0
        num_predict = 16
    }
}
if ($Model -like 'qwen3.8:*') {
    # Le smoke test vérifie le runtime, pas le raisonnement profond.
    # /api/chat sépare explicitement thinking et contenu final.
    $RequestBody.think = $false
}
$Body = $RequestBody | ConvertTo-Json -Depth 6 -Compress

try {
    $Response = Invoke-RestMethod -Method Post `
        -Uri "$OllamaEndpoint/api/chat" `
        -ContentType 'application/json' `
        -Body $Body `
        -TimeoutSec $TimeoutSeconds
}
catch {
    throw "Inférence Ollama API en échec pour $Model : $($_.Exception.Message)"
}

$Output = ([string]$Response.message.content).Trim()
if ($Output -notmatch 'LOCAL_OK') {
    throw "Smoke test inattendu pour $Model. Réponse reçue: $Output"
}

$EvalCount = 0
if ($Response.PSObject.Properties['eval_count']) {
    $EvalCount = [int]$Response.eval_count
}
$EvalDuration = 0L
if ($Response.PSObject.Properties['eval_duration']) {
    $EvalDuration = [long]$Response.eval_duration
}
$TokensPerSecond = $null
if ($EvalCount -gt 0 -and $EvalDuration -gt 0) {
    $TokensPerSecond = [math]::Round($EvalCount / $EvalDuration * 1000000000, 2)
}

$Metric = if ($null -ne $TokensPerSecond) { " ($TokensPerSecond tok/s)" } else { '' }
Write-Host "OK  Inférence locale validée avec $Model via API Ollama$Metric."

try {
    $Running = Invoke-RestMethod -Method Get `
        -Uri "$OllamaEndpoint/api/ps" `
        -TimeoutSec 5
    $Loaded = $Running.models |
        Where-Object { $_.name -eq $Model -or $_.model -eq $Model } |
        Select-Object -First 1
    if ($null -ne $Loaded) {
        $SizeBytes = [double]$Loaded.size
        $VramBytes = [double]$Loaded.size_vram
        $SizeGiB = [math]::Round($SizeBytes / 1GB, 2)
        $VramGiB = [math]::Round($VramBytes / 1GB, 2)
        $GpuPercent = if ($SizeBytes -gt 0) {
            [math]::Round(($VramBytes / $SizeBytes) * 100, 1)
        }
        else {
            0
        }
        $ContextLength = $Loaded.context_length
        Write-Host (
            "INFO Ollama mémoire $Model : VRAM=$VramGiB/$SizeGiB GiB " +
            "(~$GpuPercent% GPU), contexte alloué=$ContextLength."
        )
    }
}
catch {
    Write-Host "INFO Ollama mémoire $Model : métrique /api/ps indisponible."
}

exit 0
