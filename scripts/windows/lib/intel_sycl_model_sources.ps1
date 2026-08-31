Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-IntelSyclNativeModelOverride {
    param(
        [Parameter(Mandatory)]$RuntimeLock,
        [Parameter(Mandatory)][string]$Model
    )

    if (-not $RuntimeLock.native_model_overrides) {
        return $null
    }
    $Property = $RuntimeLock.native_model_overrides.PSObject.Properties[$Model]
    if (-not $Property) {
        return $null
    }
    return $Property.Value
}

function Get-IntelSyclManagedModelPath {
    param(
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)]$Override
    )

    $Root = Join-Path $PlatformRoot 'models\llama.cpp'
    return Join-Path $Root ([string]$Override.filename)
}

function Install-IntelSyclNativeModel {
    param(
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)][string]$Model,
        [Parameter(Mandatory)]$Override
    )

    $Target = Get-IntelSyclManagedModelPath -PlatformRoot $PlatformRoot -Override $Override
    $Directory = Split-Path -Parent $Target
    $ExpectedHash = ([string]$Override.sha256).ToLowerInvariant()
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null

    if (Test-Path -LiteralPath $Target) {
        $CurrentHash = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($CurrentHash -eq $ExpectedHash) {
            Write-Host "OK  GGUF natif llama.cpp $Model intact: $Target (SHA-256=$CurrentHash)"
            return $Target
        }
        $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
        $Quarantine = "$Target.invalid-$Stamp"
        Move-Item -LiteralPath $Target -Destination $Quarantine -Force
        Write-Warning "GGUF natif $Model invalide déplacé vers $Quarantine."
    }

    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $Curl) {
        throw 'curl.exe est requis pour le téléchargement reprenable du GGUF natif llama.cpp.'
    }

    $Partial = "$Target.partial"
    Write-Host (
        "Téléchargement GGUF natif llama.cpp pour $Model (reprenable)...`n" +
        "SOURCE=$($Override.source)`nTARGET=$Target"
    )
    & $Curl.Source `
        '--location' `
        '--fail' `
        '--retry' '3' `
        '--retry-delay' '5' `
        '--continue-at' '-' `
        '--output' $Partial `
        ([string]$Override.url)
    if ($LASTEXITCODE -ne 0) {
        throw "Téléchargement GGUF natif $Model en échec (curl code $LASTEXITCODE)."
    }

    $ActualHash = (Get-FileHash -LiteralPath $Partial -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHash) {
        Remove-Item -LiteralPath $Partial -Force -ErrorAction SilentlyContinue
        throw (
            "SHA-256 GGUF natif $Model invalide. " +
            "Attendu=$ExpectedHash Reçu=$ActualHash"
        )
    }
    Move-Item -LiteralPath $Partial -Destination $Target -Force

    $Manifest = [ordered]@{
        schema_version = '1.0.0'
        model = $Model
        source = [string]$Override.source
        filename = [string]$Override.filename
        url = [string]$Override.url
        sha256 = $ActualHash
        quantization = [string]$Override.quantization
        architecture = [string]$Override.architecture
        reason = [string]$Override.reason
        installed_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    $ManifestPath = "$Target.manifest.json"
    $Manifest | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $ManifestPath -Encoding utf8

    Write-Host "OK  GGUF natif llama.cpp $Model vérifié: $Target (SHA-256=$ActualHash)"
    return $Target
}

function Resolve-IntelSyclModelPath {
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)][string]$Model,
        [switch]$AllowDownload
    )

    $RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
    $Override = Get-IntelSyclNativeModelOverride -RuntimeLock $RuntimeLock -Model $Model
    if (-not $Override) {
        return Resolve-OllamaGgufPath -Model $Model
    }

    $Target = Get-IntelSyclManagedModelPath -PlatformRoot $PlatformRoot -Override $Override
    if (Test-Path -LiteralPath $Target) {
        $ExpectedHash = ([string]$Override.sha256).ToLowerInvariant()
        $ActualHash = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualHash -eq $ExpectedHash) {
            Write-Host "OK  Source SYCL native $Model -> $Target"
            return $Target
        }
        if (-not $AllowDownload) {
            throw "GGUF natif SYCL $Model présent mais SHA-256 invalide: $Target"
        }
    }

    if (-not $AllowDownload) {
        throw (
            "GGUF natif llama.cpp requis pour $Model mais absent: $Target. " +
            'Exécutez .\menu.ps1 -Action intel-sycl-setup.'
        )
    }
    return Install-IntelSyclNativeModel `
        -PlatformRoot $PlatformRoot -Model $Model -Override $Override
}

function New-IntelSyclModelPreset {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$PresetPath
    )

    $PlatformRoot = Get-OpenClawLocalPlatformRoot
    $Models = Get-RequiredOllamaModelList -RepoRoot $RepoRoot
    $Lines = @(
        'version = 1',
        '',
        '; Généré par OPENCLAW_LOCAL. Ne pas éditer à la main.',
        '; Qwen/Gemma réutilisent Ollama; les overrides natifs sont verrouillés par SHA-256.',
        ''
    )
    foreach ($Model in $Models) {
        $Path = Resolve-IntelSyclModelPath `
            -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot `
            -Model $Model -AllowDownload
        $Normalized = $Path -replace '\\', '/'
        $Lines += "[$Model]"
        $Lines += "model = $Normalized"
        $Lines += 'load-on-startup = false'
        $Lines += 'stop-timeout = 30'
        $Lines += ''
        Write-Host "OK  GGUF SYCL $Model -> $Path"
    }
    if (-not $PSCmdlet.ShouldProcess($PresetPath, 'Generate Intel SYCL model preset')) {
        return $Models
    }
    $Directory = Split-Path -Parent $PresetPath
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Set-Content -LiteralPath $PresetPath -Value $Lines -Encoding utf8
    return $Models
}
