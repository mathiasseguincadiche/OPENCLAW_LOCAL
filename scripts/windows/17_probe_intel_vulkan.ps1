[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateRange(60, 600)]
    [int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\intel_sycl_model_sources.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

function Get-IntelVulkanRuntimeLock {
    param([Parameter(Mandatory)][string]$RepositoryRoot)

    $LockPath = Join-Path $RepositoryRoot 'config\v1\runtime_versions.json'
    $Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json
    if (-not $Lock.llama_cpp_vulkan_probe) {
        throw 'Contrat llama_cpp_vulkan_probe absent de runtime_versions.json.'
    }
    return $Lock.llama_cpp_vulkan_probe
}

function Get-IntelVulkanPathSet {
    param(
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)]$RuntimeLock
    )

    $Root = Join-Path $PlatformRoot 'runtime\llama.cpp-vulkan'
    $VersionRoot = Join-Path $Root ([string]$RuntimeLock.release)
    $StateRoot = Join-Path $PlatformRoot 'state\intel-vulkan-probe'
    $ProofRoot = Join-Path $PlatformRoot 'proofs\intel-vulkan-probe'
    return [pscustomobject]@{
        Root = $Root
        VersionRoot = $VersionRoot
        StateRoot = $StateRoot
        ProofRoot = $ProofRoot
        Archive = Join-Path $Root ([string]$RuntimeLock.asset)
        Manifest = Join-Path $StateRoot 'runtime-manifest.json'
    }
}

function Get-IntelVulkanServerBinary {
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

function Install-IntelVulkanProbeRuntime {
    param(
        [Parameter(Mandatory)][string]$RepositoryRoot,
        [Parameter(Mandatory)][string]$PlatformRoot
    )

    $RuntimeLock = Get-IntelVulkanRuntimeLock -RepositoryRoot $RepositoryRoot
    $Paths = Get-IntelVulkanPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
    New-Item -ItemType Directory -Path $Paths.Root -Force | Out-Null
    New-Item -ItemType Directory -Path $Paths.StateRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null

    $ExpectedHash = ([string]$RuntimeLock.sha256).ToLowerInvariant()
    $ArchiveValid = $false
    if (Test-Path -LiteralPath $Paths.Archive) {
        $CurrentHash = (Get-FileHash -LiteralPath $Paths.Archive -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($CurrentHash -eq $ExpectedHash) {
            $ArchiveValid = $true
            Write-Host "OK  SHA-256 archive llama.cpp Vulkan vérifié: $CurrentHash"
        }
        else {
            Remove-Item -LiteralPath $Paths.Archive -Force
            Write-Warning 'Archive llama.cpp Vulkan invalide supprimée avant retéléchargement.'
        }
    }

    if (-not $ArchiveValid) {
        $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
        if (-not $Curl) {
            throw 'curl.exe est requis pour télécharger le runtime llama.cpp Vulkan.'
        }
        $Partial = "$($Paths.Archive).partial"
        Write-Host "Téléchargement llama.cpp Vulkan $($RuntimeLock.release) (reprenable)..."
        & $Curl.Source `
            '--location' '--fail' '--retry' '3' '--retry-delay' '5' `
            '--continue-at' '-' '--output' $Partial ([string]$RuntimeLock.url)
        if ($LASTEXITCODE -ne 0) {
            throw "Téléchargement llama.cpp Vulkan en échec (curl code $LASTEXITCODE)."
        }
        $ActualHash = (Get-FileHash -LiteralPath $Partial -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualHash -ne $ExpectedHash) {
            Remove-Item -LiteralPath $Partial -Force -ErrorAction SilentlyContinue
            throw "SHA-256 llama.cpp Vulkan invalide. Attendu=$ExpectedHash Reçu=$ActualHash"
        }
        Move-Item -LiteralPath $Partial -Destination $Paths.Archive -Force
        Write-Host "OK  SHA-256 archive llama.cpp Vulkan vérifié: $ActualHash"
    }

    $Existing = Get-IntelVulkanServerBinary -VersionRoot $Paths.VersionRoot
    if ($Existing -and (Test-Path -LiteralPath $Paths.Manifest)) {
        try {
            $Manifest = Get-Content -Raw -LiteralPath $Paths.Manifest | ConvertFrom-Json
            $ServerHash = (Get-FileHash -LiteralPath $Existing -Algorithm SHA256).Hash.ToLowerInvariant()
            if (
                [string]$Manifest.release -eq [string]$RuntimeLock.release -and
                ([string]$Manifest.archive_sha256).ToLowerInvariant() -eq $ExpectedHash -and
                ([string]$Manifest.server_sha256).ToLowerInvariant() -eq $ServerHash
            ) {
                Write-Host "OK  Runtime llama.cpp Vulkan $($RuntimeLock.release) intact: $Existing"
                return $Existing
            }
        }
        catch {
            Write-Warning 'Manifeste Vulkan illisible; réextraction depuis l''archive vérifiée.'
        }
    }

    if (Test-Path -LiteralPath $Paths.VersionRoot) {
        Remove-Item -LiteralPath $Paths.VersionRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Paths.VersionRoot -Force | Out-Null
    Expand-Archive -LiteralPath $Paths.Archive -DestinationPath $Paths.VersionRoot -Force
    $Binary = Get-IntelVulkanServerBinary -VersionRoot $Paths.VersionRoot
    if (-not $Binary) {
        throw 'llama-server.exe absent du runtime Vulkan extrait.'
    }
    $BinaryHash = (Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash.ToLowerInvariant()
    [ordered]@{
        schema_version = '1.0.0'
        release = [string]$RuntimeLock.release
        release_commit = [string]$RuntimeLock.release_commit
        archive_sha256 = $ExpectedHash
        server_sha256 = $BinaryHash
        binary = $Binary
        installed_at = [DateTimeOffset]::UtcNow.ToString('o')
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Paths.Manifest -Encoding utf8
    Write-Host "OK  Runtime llama.cpp Vulkan installé: $Binary (SHA-256=$BinaryHash)"
    return $Binary
}

function Get-FreeLoopbackTcpPort {
    $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    try {
        $Listener.Start()
        return ([System.Net.IPEndPoint]$Listener.LocalEndpoint).Port
    }
    finally {
        $Listener.Stop()
    }
}

function Resolve-IntelArcB580VulkanDevice {
    param([Parameter(Mandatory)][string]$ServerBinary)

    $Output = @(& $ServerBinary --list-devices 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "llama-server Vulkan --list-devices a échoué (code $LASTEXITCODE)."
    }
    $Text = $Output -join "`n"
    $B580Line = $Output |
        Where-Object { [string]$_ -match '(?i)Intel.*Arc.*B580|Arc.*B580.*Intel' } |
        Select-Object -First 1
    if (-not $B580Line) {
        throw "Runtime Vulkan présent mais Intel Arc B580 absente de --list-devices.`n$Text"
    }
    $DeviceMatch = [regex]::Match([string]$B580Line, '^\s*([A-Za-z]+\d+)\s*:')
    if (-not $DeviceMatch.Success) {
        throw "Impossible d'extraire l'ID device Vulkan B580 depuis: $B580Line"
    }
    $Device = $DeviceMatch.Groups[1].Value
    Write-Host "OK  Intel Arc B580 détectée via llama.cpp Vulkan: $Device"
    Write-Host $Text
    return [pscustomobject]@{
        id = $Device
        evidence = $Text
    }
}

function Wait-LlamaCppProbeApi {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)]$Process,
        [int]$TimeoutSeconds = 180
    )

    $Deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        if ($Process.HasExited) {
            throw "llama-server Vulkan a quitté prématurément (code $($Process.ExitCode))."
        }
        try {
            $Response = Invoke-RestMethod -Method Get -Uri "$BaseUrl/models" -TimeoutSec 3
            if ($Response.data) {
                return $Response
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ([DateTimeOffset]::UtcNow -lt $Deadline)
    throw "API llama.cpp Vulkan non prête après $TimeoutSeconds s: $BaseUrl"
}

function Get-LogTailText {
    param(
        [Parameter(Mandatory)][string]$Path,
        [int]$Lines = 120
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return '<log absent>'
    }
    return ((Get-Content -LiteralPath $Path -Tail $Lines) -join "`n")
}

function Invoke-LlamaCppVulkanCase {
    param(
        [Parameter(Mandatory)][string]$ServerBinary,
        [Parameter(Mandatory)][string]$ModelPath,
        [Parameter(Mandatory)][string]$Model,
        [Parameter(Mandatory)][string]$Device,
        [Parameter(Mandatory)]$RuntimeLock,
        [Parameter(Mandatory)][string]$ProofRoot,
        [Parameter(Mandatory)][string]$Prompt,
        [int]$MaxTokens = 128,
        [int]$TimeoutSeconds = 300
    )

    $Port = Get-FreeLoopbackTcpPort
    $BaseUrl = "http://127.0.0.1:$Port/v1"
    $SafeModel = $Model -replace '[^a-zA-Z0-9._-]', '_'
    $StdoutPath = Join-Path $ProofRoot "$SafeModel.stdout.log"
    $StderrPath = Join-Path $ProofRoot "$SafeModel.stderr.log"
    Remove-Item -LiteralPath $StdoutPath, $StderrPath -Force -ErrorAction SilentlyContinue
    $Arguments = @(
        '--host', '127.0.0.1',
        '--port', [string]$Port,
        '--model', $ModelPath,
        '--alias', $Model,
        '--ctx-size', [string]$RuntimeLock.context_tokens,
        '--gpu-layers', [string]$RuntimeLock.gpu_layers,
        '--parallel', [string]$RuntimeLock.parallel,
        '--fit', 'on',
        '--device', $Device,
        '--jinja',
        '--metrics',
        '--offline'
    )

    Write-Host "VULKAN_PROBE model=$Model device=$Device gpu_layers=$($RuntimeLock.gpu_layers) parallel=$($RuntimeLock.parallel)"
    $Process = $null
    try {
        $Process = Start-Process -FilePath $ServerBinary -ArgumentList $Arguments `
            -WorkingDirectory (Split-Path -Parent $ServerBinary) `
            -RedirectStandardOutput $StdoutPath `
            -RedirectStandardError $StderrPath `
            -WindowStyle Hidden -PassThru
        $null = Wait-LlamaCppProbeApi -BaseUrl $BaseUrl -Process $Process -TimeoutSeconds 180

        $Body = @{
            model = $Model
            messages = @(
                @{
                    role = 'user'
                    content = $Prompt
                }
            )
            temperature = 0
            max_tokens = $MaxTokens
            stream = $false
            chat_template_kwargs = @{
                enable_thinking = $false
            }
        } | ConvertTo-Json -Depth 8 -Compress

        $Started = [DateTimeOffset]::UtcNow
        $Response = Invoke-RestMethod -Method Post `
            -Uri "$BaseUrl/chat/completions" `
            -ContentType 'application/json' `
            -Body $Body `
            -TimeoutSec $TimeoutSeconds
        $WallMs = ([DateTimeOffset]::UtcNow - $Started).TotalMilliseconds
        $Choices = @($Response.choices)
        if ($Choices.Count -lt 1) {
            throw "llama.cpp Vulkan n'a retourné aucun choix pour $Model."
        }
        $Content = [string]$Choices[0].message.content
        if (-not $Content.Trim()) {
            throw "Réponse finale Vulkan vide pour $Model."
        }
        $Timings = $Response.timings
        $Usage = $Response.usage
        $Result = [pscustomobject]@{
            model = $Model
            model_path = $ModelPath
            wall_ms = [math]::Round($WallMs, 1)
            prompt_tokens = if ($Usage) { [int]$Usage.prompt_tokens } else { 0 }
            output_tokens = if ($Usage) { [int]$Usage.completion_tokens } else { 0 }
            prompt_tokens_per_second = if ($Timings) { $Timings.prompt_per_second } else { $null }
            tokens_per_second = if ($Timings) { $Timings.predicted_per_second } else { $null }
            finish_reason = [string]$Choices[0].finish_reason
            content = $Content.Trim()
            stdout = $StdoutPath
            stderr = $StderrPath
            ok = $true
        }
        Write-Host (
            "OK  Vulkan ${Model}: wall=$($Result.wall_ms)ms " +
            "tok/s=$($Result.tokens_per_second) " +
            "prompt_tok/s=$($Result.prompt_tokens_per_second)"
        )
        return $Result
    }
    catch {
        $Tail = Get-LogTailText -Path $StderrPath
        throw "$($_.Exception.Message)`nDernières lignes llama.cpp Vulkan:`n$Tail"
    }
    finally {
        if ($Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            $null = $Process.WaitForExit(10000)
        }
    }
}

function Get-LatestBackendBaseline {
    param([Parameter(Mandatory)][string]$RepositoryRoot)

    $ResultsRoot = Join-Path $RepositoryRoot 'benchmarks\results'
    if (-not (Test-Path -LiteralPath $ResultsRoot)) {
        return $null
    }
    $Files = @(
        Get-ChildItem -LiteralPath $ResultsRoot -Filter 'backend_compare_b580_*.json' -File |
            Sort-Object LastWriteTime -Descending
    )
    foreach ($File in $Files) {
        try {
            $Data = Get-Content -Raw -LiteralPath $File.FullName | ConvertFrom-Json
            $SchemaProperty = $Data.PSObject.Properties['schema_version']
            $ProtocolProperty = $Data.PSObject.Properties['protocol']
            $SummaryProperty = $Data.PSObject.Properties['summary']
            if (-not $SchemaProperty -or -not $ProtocolProperty -or -not $SummaryProperty) {
                Write-Warning "Baseline ignorée (structure incomplète): $($File.FullName)"
                continue
            }
            $Protocol = $ProtocolProperty.Value
            $Summary = $SummaryProperty.Value
            $IsolationProperty = $Protocol.PSObject.Properties['gpu_memory_isolation_between_backends']
            $ModelsProperty = $Summary.PSObject.Properties['models']
            if (
                [string]$SchemaProperty.Value -ne '1.5.0' -or
                -not $IsolationProperty -or
                -not [bool]$IsolationProperty.Value -or
                -not $ModelsProperty
            ) {
                Write-Warning "Baseline ignorée (protocole non isolé ou schéma incompatible): $($File.FullName)"
                continue
            }
            return [pscustomobject]@{
                path = $File.FullName
                data = $Data
            }
        }
        catch {
            Write-Warning "Baseline ignorée (JSON invalide): $($File.FullName)"
            continue
        }
    }
    return $null
}

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelVulkanRuntimeLock -RepositoryRoot $RepoRoot
$Prompt = "Réponds en JSON compact avec exactement les clés diagnostic, action, rollback. Incident: un Deployment Kubernetes reste à 0/2 Ready après changement d'image. N'invente pas la cause; donne une vérification concrète."

if ($DryRun) {
    Write-Host '[DRY-RUN] Probe d''isolation llama.cpp Vulkan sur Intel Arc B580.'
    Write-Host "[DRY-RUN] Release=$($RuntimeLock.release) Asset=$($RuntimeLock.asset)"
    Write-Host "[DRY-RUN] SHA-256=$($RuntimeLock.sha256)"
    Write-Host "[DRY-RUN] context=$($RuntimeLock.context_tokens) gpu_layers=$($RuntimeLock.gpu_layers) parallel=$($RuntimeLock.parallel)"
    Write-Host '[DRY-RUN] Réutiliser exactement les sources GGUF effectives du backend llama.cpp/SYCL.'
    Write-Host '[DRY-RUN] Démarrer un serveur Vulkan éphémère par modèle, puis l''arrêter après une requête.'
    Write-Host '[DRY-RUN] Baseline acceptée uniquement si schéma 1.5.0 avec isolation mémoire GPU.'
    Write-Host '[DRY-RUN] Aucune modification OpenClaw et aucune promotion backend.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
$Binary = Install-IntelVulkanProbeRuntime -RepositoryRoot $RepoRoot -PlatformRoot $PlatformRoot
$Driver = Get-IntelArcB580DriverInfo
Write-Host "OK  Pilote Intel B580 détecté: $($Driver.driver_version)"
$Device = Resolve-IntelArcB580VulkanDevice -ServerBinary $Binary
$Models = Get-RequiredOllamaModelList -RepoRoot $RepoRoot
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$Paths = Get-IntelVulkanPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
$ProofDirectory = Join-Path $Paths.ProofRoot "probe-$Stamp"
New-Item -ItemType Directory -Path $ProofDirectory -Force | Out-Null

$Results = @()
foreach ($Model in $Models) {
    $ModelPath = Resolve-IntelSyclModelPath `
        -RepoRoot $RepoRoot -PlatformRoot $PlatformRoot -Model $Model
    $Results += Invoke-LlamaCppVulkanCase `
        -ServerBinary $Binary -ModelPath $ModelPath -Model $Model `
        -Device ([string]$Device.id) -RuntimeLock $RuntimeLock `
        -ProofRoot $ProofDirectory -Prompt $Prompt -TimeoutSeconds $TimeoutSeconds
}

$Baseline = Get-LatestBackendBaseline -RepositoryRoot $RepoRoot
$Comparisons = @()
foreach ($Result in $Results) {
    $OllamaTps = $null
    $SyclTps = $null
    if ($Baseline) {
        $ModelProperty = $Baseline.data.summary.models.PSObject.Properties[[string]$Result.model]
        if ($ModelProperty) {
            $ModelReport = $ModelProperty.Value
            $OllamaProperty = $ModelReport.PSObject.Properties['ollama-vulkan']
            $SyclProperty = $ModelReport.PSObject.Properties['llama-cpp-sycl']
            if ($OllamaProperty) {
                $OllamaTps = $OllamaProperty.Value.median_tokens_per_second
            }
            if ($SyclProperty) {
                $SyclTps = $SyclProperty.Value.median_tokens_per_second
            }
        }
    }
    $VulkanTps = if ($null -ne $Result.tokens_per_second) {
        [double]$Result.tokens_per_second
    }
    else {
        $null
    }
    $VsOllama = if (
        $null -ne $VulkanTps -and
        $null -ne $OllamaTps -and
        [double]$OllamaTps -ne 0
    ) {
        [double]$VulkanTps / [double]$OllamaTps
    }
    else {
        $null
    }
    $VsSycl = if (
        $null -ne $VulkanTps -and
        $null -ne $SyclTps -and
        [double]$SyclTps -ne 0
    ) {
        [double]$VulkanTps / [double]$SyclTps
    }
    else {
        $null
    }
    $Comparisons += [pscustomobject]@{
        model = [string]$Result.model
        llama_cpp_vulkan_tps = $VulkanTps
        ollama_vulkan_tps = $OllamaTps
        llama_cpp_sycl_tps = $SyclTps
        vulkan_speedup_vs_ollama = $VsOllama
        vulkan_speedup_vs_sycl = $VsSycl
    }
}

$Proof = [ordered]@{
    schema_version = '1.1.0'
    probed_at = [DateTimeOffset]::UtcNow.ToString('o')
    purpose = [string]$RuntimeLock.purpose
    release = [string]$RuntimeLock.release
    release_commit = [string]$RuntimeLock.release_commit
    asset = [string]$RuntimeLock.asset
    archive_sha256 = [string]$RuntimeLock.sha256
    binary = $Binary
    binary_sha256 = (Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash.ToLowerInvariant()
    driver = $Driver
    device = [string]$Device.id
    device_evidence = [string]$Device.evidence
    context_tokens = [int]$RuntimeLock.context_tokens
    gpu_layers = [string]$RuntimeLock.gpu_layers
    parallel = [int]$RuntimeLock.parallel
    prompt = $Prompt
    max_tokens = 128
    thinking = 'disabled'
    baseline_required_schema = '1.5.0'
    baseline = if ($Baseline) { [string]$Baseline.path } else { $null }
    results = @($Results)
    comparisons = @($Comparisons)
    openclaw_modified = $false
    promotion_allowed = $false
}
$ProofPath = Join-Path $ProofDirectory 'vulkan_probe.json'
$Proof | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ProofPath -Encoding utf8
Write-Host "INTEL_VULKAN_PROBE=$ProofPath"
foreach ($Comparison in $Comparisons) {
    $VulkanText = if ($null -ne $Comparison.llama_cpp_vulkan_tps) {
        [string][double]$Comparison.llama_cpp_vulkan_tps
    }
    else {
        'n/a'
    }
    $VsOllamaText = if ($null -ne $Comparison.vulkan_speedup_vs_ollama) {
        '{0:N2}x' -f [double]$Comparison.vulkan_speedup_vs_ollama
    }
    else {
        'n/a'
    }
    $VsSyclText = if ($null -ne $Comparison.vulkan_speedup_vs_sycl) {
        '{0:N2}x' -f [double]$Comparison.vulkan_speedup_vs_sycl
    }
    else {
        'n/a'
    }
    Write-Host (
        "SUMMARY $($Comparison.model) llama_cpp_vulkan=$VulkanText " +
        "vulkan_vs_ollama=$VsOllamaText vulkan_vs_sycl=$VsSyclText"
    )
}
Write-Host 'PROMOTION_ALLOWED=false'
exit 0
