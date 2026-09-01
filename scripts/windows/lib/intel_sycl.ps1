Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-OpenClawLocalPlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Get-IntelSyclRuntimeLock {
    param([Parameter(Mandatory)][string]$RepoRoot)

    $LockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
    if (-not (Test-Path -LiteralPath $LockPath)) {
        throw "Contrat runtime introuvable: $LockPath"
    }
    $Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json
    if (-not $Lock.llama_cpp_sycl) {
        throw 'Contrat llama_cpp_sycl absent de runtime_versions.json.'
    }
    return $Lock.llama_cpp_sycl
}

function Get-IntelSyclPathSet {
    param(
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)]$RuntimeLock
    )

    $Root = Join-Path $PlatformRoot 'runtime\llama.cpp-sycl'
    $VersionRoot = Join-Path $Root ([string]$RuntimeLock.release)
    $StateRoot = Join-Path $PlatformRoot 'state\intel-sycl'
    $ProofRoot = Join-Path $PlatformRoot 'proofs\intel-sycl'
    return [pscustomobject]@{
        Root = $Root
        VersionRoot = $VersionRoot
        StateRoot = $StateRoot
        ProofRoot = $ProofRoot
        Archive = Join-Path $Root ([string]$RuntimeLock.asset)
        Manifest = Join-Path $StateRoot 'runtime-manifest.json'
        Preset = Join-Path $StateRoot 'models.ini'
        ProcessState = Join-Path $StateRoot 'server.json'
        StdoutLog = Join-Path $ProofRoot 'llama-server.stdout.log'
        StderrLog = Join-Path $ProofRoot 'llama-server.stderr.log'
    }
}

function Get-IntelSyclServerBinary {
    param([Parameter(Mandatory)][string]$VersionRoot)

    if (-not (Test-Path -LiteralPath $VersionRoot)) {
        return $null
    }
    $Binary = Get-ChildItem -LiteralPath $VersionRoot -Filter 'llama-server.exe' -File -Recurse |
        Select-Object -First 1
    if ($Binary) {
        return $Binary.FullName
    }
    return $null
}

function Get-IntelArcB580DriverInfo {
    $Adapter = Get-CimInstance Win32_VideoController -ErrorAction Stop |
        Where-Object { [string]$_.Name -match '(?i)Intel.*Arc.*B580|Arc.*B580.*Intel' } |
        Select-Object -First 1
    if (-not $Adapter) {
        throw 'Intel Arc B580 absente de Win32_VideoController.'
    }
    return [pscustomobject]@{
        name = [string]$Adapter.Name
        driver_version = [string]$Adapter.DriverVersion
        pnp_device_id = [string]$Adapter.PNPDeviceID
    }
}

function Install-IntelSyclRuntime {
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$PlatformRoot
    )

    $RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
    $Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
    New-Item -ItemType Directory -Path $Paths.Root -Force | Out-Null
    New-Item -ItemType Directory -Path $Paths.StateRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null

    if (-not (Test-Path -LiteralPath $Paths.Archive)) {
        Write-Host "Téléchargement llama.cpp SYCL $($RuntimeLock.release)..."
        Invoke-WebRequest -Uri ([string]$RuntimeLock.url) -OutFile $Paths.Archive -UseBasicParsing
    }

    $ActualArchiveHash = (
        Get-FileHash -LiteralPath $Paths.Archive -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    $ExpectedArchiveHash = ([string]$RuntimeLock.sha256).ToLowerInvariant()
    if ($ActualArchiveHash -ne $ExpectedArchiveHash) {
        Remove-Item -LiteralPath $Paths.Archive -Force -ErrorAction SilentlyContinue
        throw (
            'SHA-256 llama.cpp SYCL invalide. ' +
            "Attendu=$ExpectedArchiveHash Reçu=$ActualArchiveHash"
        )
    }
    Write-Host "OK  SHA-256 archive llama.cpp SYCL vérifié: $ActualArchiveHash"

    $Existing = Get-IntelSyclServerBinary -VersionRoot $Paths.VersionRoot
    if ($Existing -and (Test-Path -LiteralPath $Paths.Manifest)) {
        try {
            $Manifest = Get-Content -Raw -LiteralPath $Paths.Manifest | ConvertFrom-Json
            $CurrentServerHash = (
                Get-FileHash -LiteralPath $Existing -Algorithm SHA256
            ).Hash.ToLowerInvariant()
            $ManifestServerHash = ([string]$Manifest.server_sha256).ToLowerInvariant()
            $ManifestArchiveHash = ([string]$Manifest.archive_sha256).ToLowerInvariant()
            if (
                [string]$Manifest.release -eq [string]$RuntimeLock.release -and
                $ManifestArchiveHash -eq $ExpectedArchiveHash -and
                $CurrentServerHash -eq $ManifestServerHash
            ) {
                Write-Host (
                    "OK  Runtime Intel SYCL $($RuntimeLock.release) intact: " +
                    "$Existing (SHA-256=$CurrentServerHash)"
                )
                return $Existing
            }
            Write-Warning "Dérive d'intégrité du runtime Intel SYCL; réextraction depuis l'archive vérifiée."
        }
        catch {
            Write-Warning (
                'Manifeste Intel SYCL illisible ou incohérent; ' +
                "réextraction depuis l'archive vérifiée."
            )
        }
    }
    elseif ($Existing) {
        Write-Warning "Runtime Intel SYCL sans manifeste d'intégrité; réextraction propre."
    }

    if (Test-Path -LiteralPath $Paths.VersionRoot) {
        Remove-Item -LiteralPath $Paths.VersionRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Paths.VersionRoot -Force | Out-Null
    Expand-Archive -LiteralPath $Paths.Archive -DestinationPath $Paths.VersionRoot -Force

    $Binary = Get-IntelSyclServerBinary -VersionRoot $Paths.VersionRoot
    if (-not $Binary) {
        throw "llama-server.exe absent après extraction de $($RuntimeLock.asset)."
    }
    $ServerHash = (
        Get-FileHash -LiteralPath $Binary -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    $InstallManifest = [ordered]@{
        schema_version = '1.0.0'
        release = [string]$RuntimeLock.release
        release_commit = [string]$RuntimeLock.release_commit
        archive = [string]$RuntimeLock.asset
        archive_sha256 = $ExpectedArchiveHash
        server_sha256 = $ServerHash
        binary = $Binary
        installed_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    $InstallManifest | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $Paths.Manifest -Encoding utf8
    Write-Host "OK  Runtime Intel SYCL installé et manifesté: $Binary"
    Write-Host "OK  SHA-256 llama-server.exe: $ServerHash"
    return $Binary
}

function Get-RequiredOllamaModelList {
    param([Parameter(Mandatory)][string]$RepoRoot)

    $ListModels = Join-Path $RepoRoot 'scripts\20_list_models.py'
    $Models = @(& python $ListModels --provider ollama --required)
    if ($LASTEXITCODE -ne 0) {
        throw 'Impossible de lire les modèles required depuis model_catalog.yaml.'
    }
    $Models = @(
        $Models |
            Where-Object { $_ -and $_.Trim() } |
            ForEach-Object { $_.Trim() }
    )
    if ($Models.Count -ne 3) {
        throw "La flotte Intel SYCL exige exactement 3 modèles; détectés: $($Models.Count)."
    }
    return $Models
}

function Resolve-OllamaGgufPath {
    param([Parameter(Mandatory)][string]$Model)

    $Output = @(& ollama show $Model --modelfile 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de lire le Modelfile Ollama pour $Model."
    }
    $FromLine = $Output |
        Where-Object { [string]$_ -match '^\s*FROM\s+' } |
        Select-Object -First 1
    if (-not $FromLine) {
        throw "Ligne FROM absente du Modelfile Ollama pour $Model."
    }
    $Raw = ([string]$FromLine -replace '^\s*FROM\s+', '').Trim().Trim('"')
    if (-not (Test-Path -LiteralPath $Raw)) {
        throw (
            "Le modèle Ollama $Model ne référence pas un blob GGUF local " +
            "exploitable: $Raw"
        )
    }
    return (Resolve-Path -LiteralPath $Raw).Path
}

function New-IntelSyclModelPreset {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$PresetPath
    )

    $Models = Get-RequiredOllamaModelList -RepoRoot $RepoRoot
    $Lines = @(
        'version = 1',
        '',
        '; Généré par OPENCLAW_LOCAL. Ne pas éditer à la main.',
        '; Les poids restent ceux déjà présents dans le cache Ollama.',
        ''
    )
    foreach ($Model in $Models) {
        $Path = Resolve-OllamaGgufPath -Model $Model
        $Normalized = $Path -replace '\\', '/'
        $Lines += "[$Model]"
        $Lines += "model = $Normalized"
        $Lines += 'load-on-startup = false'
        $Lines += 'stop-timeout = 30'
        $Lines += ''
        Write-Host "OK  GGUF $Model -> $Path"
    }
    if (-not $PSCmdlet.ShouldProcess($PresetPath, 'Generate Intel SYCL model preset')) {
        return $Models
    }
    $Directory = Split-Path -Parent $PresetPath
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Set-Content -LiteralPath $PresetPath -Value $Lines -Encoding utf8
    return $Models
}

function Test-IntelArcB580SyclDevice {
    param(
        [Parameter(Mandatory)][string]$ServerBinary,
        [Parameter(Mandatory)]$RuntimeLock
    )

    $PreviousSelector = $env:ONEAPI_DEVICE_SELECTOR
    try {
        $env:ONEAPI_DEVICE_SELECTOR = [string]$RuntimeLock.oneapi_device_selector
        $Output = @(& $ServerBinary --list-devices 2>&1)
        if ($LASTEXITCODE -ne 0) {
            throw "llama-server --list-devices a échoué (code $LASTEXITCODE)."
        }
        $Text = $Output -join "`n"
        if ($Text -notmatch '(?im)\bSYCL0\b') {
            throw (
                'Aucun device SYCL0 détecté sous ' +
                "ONEAPI_DEVICE_SELECTOR=$($RuntimeLock.oneapi_device_selector)."
            )
        }
        if ($Text -notmatch '(?im)Intel.*Arc.*B580|Arc.*B580.*Intel') {
            throw (
                "SYCL est présent mais la B580 n'est pas identifiée dans " +
                "la liste des devices.`n$Text"
            )
        }
        Write-Host (
            'OK  Intel Arc B580 détectée via SYCL/Level Zero ' +
            "($($RuntimeLock.oneapi_device_selector))."
        )
        Write-Host $Text
        return $Text
    }
    finally {
        if ($null -eq $PreviousSelector) {
            Remove-Item Env:ONEAPI_DEVICE_SELECTOR -ErrorAction SilentlyContinue
        }
        else {
            $env:ONEAPI_DEVICE_SELECTOR = $PreviousSelector
        }
    }
}

function Stop-IntelSyclServer {
    [CmdletBinding(SupportsShouldProcess)]
    param([Parameter(Mandatory)][string]$StatePath)

    if (-not (Test-Path -LiteralPath $StatePath)) {
        return
    }
    if (-not $PSCmdlet.ShouldProcess(
        $StatePath,
        'Stop tracked Intel SYCL server and remove process state'
    )) {
        return
    }
    try {
        $State = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
        $Process = Get-Process -Id ([int]$State.pid) -ErrorAction SilentlyContinue
        if ($Process) {
            Stop-Process -Id $Process.Id -Force
            $null = $Process.WaitForExit(10000)
            Write-Host "OK  llama-server Intel SYCL arrêté (PID=$($Process.Id))."
        }
    }
    finally {
        Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
    }
}

function Wait-IntelSyclApi {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [int]$TimeoutSeconds = 120
    )

    $Deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        try {
            $Response = Invoke-RestMethod -Method Get `
                -Uri "$BaseUrl/models?reload=1" -TimeoutSec 5
            if ($Response.data) {
                return $Response
            }
        }
        catch {
            Start-Sleep -Milliseconds 1000
        }
    } while ([DateTimeOffset]::UtcNow -lt $Deadline)
    throw "API llama.cpp Intel SYCL non prête après $TimeoutSeconds s: $BaseUrl"
}

function Start-IntelSyclServer {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string]$PlatformRoot,
        [int]$TimeoutSeconds = 120
    )

    $RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
    $Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
    $Binary = Get-IntelSyclServerBinary -VersionRoot $Paths.VersionRoot
    if (-not $Binary) {
        throw 'Runtime llama.cpp SYCL absent. Exécutez intel-sycl-setup.'
    }
    $Driver = Get-IntelArcB580DriverInfo
    Write-Host "OK  Pilote Intel B580 détecté: $($Driver.driver_version)"
    $null = Test-IntelArcB580SyclDevice -ServerBinary $Binary -RuntimeLock $RuntimeLock
    if (-not $PSCmdlet.ShouldProcess(
        ([string]$RuntimeLock.endpoint),
        'Start Intel SYCL llama-server'
    )) {
        return $null
    }
    $Models = New-IntelSyclModelPreset -RepoRoot $RepoRoot -PresetPath $Paths.Preset -Confirm:$false
    $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false

    $Listeners = @(
        Get-NetTCPConnection -LocalPort ([int]$RuntimeLock.listen_port) `
            -State Listen -ErrorAction SilentlyContinue
    )
    if ($Listeners.Count -gt 0) {
        $OwnerIds = @(
            $Listeners |
                ForEach-Object { [int]$_.OwningProcess } |
                Sort-Object -Unique
        )
        throw (
            "Port $($RuntimeLock.listen_port) déjà occupé par PID=" +
            ($OwnerIds -join ',') +
            '. Aucun processus non suivi ne sera réutilisé ni arrêté.'
        )
    }

    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
    Remove-Item -LiteralPath $Paths.StdoutLog, $Paths.StderrLog `
        -Force -ErrorAction SilentlyContinue

    $Arguments = @(
        '--models-preset', $Paths.Preset,
        '--models-max', [string]$RuntimeLock.models_max,
        '--models-autoload',
        '--host', [string]$RuntimeLock.listen_host,
        '--port', [string]$RuntimeLock.listen_port,
        '--ctx-size', [string]$RuntimeLock.context_tokens,
        '--gpu-layers', [string]$RuntimeLock.gpu_layers,
        '--device', [string]$RuntimeLock.device,
        '--jinja',
        '--metrics',
        '--offline'
    )

    $PreviousSelector = $env:ONEAPI_DEVICE_SELECTOR
    try {
        $env:ONEAPI_DEVICE_SELECTOR = [string]$RuntimeLock.oneapi_device_selector
        $Process = Start-Process -FilePath $Binary -ArgumentList $Arguments `
            -WorkingDirectory (Split-Path -Parent $Binary) `
            -RedirectStandardOutput $Paths.StdoutLog `
            -RedirectStandardError $Paths.StderrLog `
            -WindowStyle Hidden -PassThru
    }
    finally {
        if ($null -eq $PreviousSelector) {
            Remove-Item Env:ONEAPI_DEVICE_SELECTOR -ErrorAction SilentlyContinue
        }
        else {
            $env:ONEAPI_DEVICE_SELECTOR = $PreviousSelector
        }
    }

    $State = [ordered]@{
        pid = $Process.Id
        started_at = [DateTimeOffset]::UtcNow.ToString('o')
        release = [string]$RuntimeLock.release
        endpoint = [string]$RuntimeLock.endpoint
        device = [string]$RuntimeLock.device
        oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
        models_max = [int]$RuntimeLock.models_max
        models = @($Models)
        driver = $Driver
        stdout = $Paths.StdoutLog
        stderr = $Paths.StderrLog
    }
    $State | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $Paths.ProcessState -Encoding utf8

    try {
        $Api = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) `
            -TimeoutSeconds $TimeoutSeconds
        if ($Process.HasExited) {
            throw "llama-server Intel SYCL a quitté prématurément (code $($Process.ExitCode))."
        }
    }
    catch {
        $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
        $Tail = if (Test-Path -LiteralPath $Paths.StderrLog) {
            (Get-Content -LiteralPath $Paths.StderrLog -Tail 80) -join "`n"
        }
        else {
            '<aucun stderr>'
        }
        throw "$($_.Exception.Message)`nDernières lignes llama-server:`n$Tail"
    }

    $Advertised = @($Api.data | ForEach-Object { [string]$_.id })
    foreach ($Model in $Models) {
        if ($Advertised -notcontains $Model) {
            $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
            throw "Le routeur Intel SYCL n'annonce pas le modèle requis: $Model"
        }
    }
    Write-Host (
        "OK  Routeur llama.cpp Intel SYCL prêt PID=$($Process.Id) " +
        "endpoint=$($RuntimeLock.endpoint)."
    )
    return [pscustomobject]@{
        Process = $Process
        RuntimeLock = $RuntimeLock
        Paths = $Paths
        Models = $Models
        Driver = $Driver
        Api = $Api
    }
}

function Invoke-IntelSyclChatSmoke {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Model,
        [int]$TimeoutSeconds = 300
    )

    $Body = @{
        model = $Model
        messages = @(
            @{
                role = 'user'
                content = 'Réponds uniquement LOCAL_OK.'
            }
        )
        temperature = 0
        max_tokens = 16
        stream = $false
    } | ConvertTo-Json -Depth 8 -Compress
    $Started = [DateTimeOffset]::UtcNow
    $Response = Invoke-RestMethod -Method Post `
        -Uri "$BaseUrl/chat/completions" `
        -ContentType 'application/json' `
        -Body $Body `
        -TimeoutSec $TimeoutSeconds
    $ElapsedMs = ([DateTimeOffset]::UtcNow - $Started).TotalMilliseconds
    $Content = [string]$Response.choices[0].message.content
    if ($Content -notmatch 'LOCAL_OK') {
        throw "Smoke Intel SYCL inattendu pour $Model : $Content"
    }
    $Timings = $Response.timings
    return [pscustomobject]@{
        model = $Model
        wall_ms = [math]::Round($ElapsedMs, 1)
        prompt_tokens_per_second = if ($Timings) {
            $Timings.prompt_per_second
        }
        else {
            $null
        }
        tokens_per_second = if ($Timings) {
            $Timings.predicted_per_second
        }
        else {
            $null
        }
        predicted_tokens = if ($Timings) {
            $Timings.predicted_n
        }
        else {
            $null
        }
        finish_reason = [string]$Response.choices[0].finish_reason
        ok = $true
    }
}