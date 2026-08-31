[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateSet('qwen3.8:27b', 'gemma4:26b', 'devstral-small-2:24b')]
    [string]$Model = 'devstral-small-2:24b',
    [ValidateRange(30, 600)]
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

function Get-FreeLoopbackTcpPort {
    $Listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    try {
        $Listener.Start()
        return ([System.Net.IPEndPoint]$Listener.LocalEndpoint).Port
    }
    finally {
        $Listener.Stop()
    }
}

function Get-LogTailText {
    param(
        [Parameter(Mandatory)][string]$Path,
        [int]$Lines = 160
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return '<log absent>'
    }
    return ((Get-Content -LiteralPath $Path -Tail $Lines) -join "`n")
}

function Invoke-DirectIntelSyclLoadProbe {
    param(
        [Parameter(Mandatory)][string]$ServerBinary,
        [Parameter(Mandatory)][string]$ModelPath,
        [Parameter(Mandatory)][string]$ModelAlias,
        [Parameter(Mandatory)][string]$Scenario,
        [Parameter(Mandatory)][string]$ProofDirectory,
        [Parameter(Mandatory)]$RuntimeLock,
        [Parameter(Mandatory)][ValidateSet('on', 'off')][string]$Fit,
        [Parameter(Mandatory)][string]$GpuLayers,
        [Parameter(Mandatory)][bool]$UseSyclDevice,
        [Parameter(Mandatory)][int]$TimeoutSeconds
    )

    $Port = Get-FreeLoopbackTcpPort
    $StdoutPath = Join-Path $ProofDirectory "$Scenario.stdout.log"
    $StderrPath = Join-Path $ProofDirectory "$Scenario.stderr.log"
    Remove-Item -LiteralPath $StdoutPath, $StderrPath -Force -ErrorAction SilentlyContinue

    $Arguments = @(
        '--host', '127.0.0.1',
        '--port', [string]$Port,
        '--model', $ModelPath,
        '--alias', $ModelAlias,
        '--ctx-size', [string]$RuntimeLock.context_tokens,
        '--gpu-layers', $GpuLayers,
        '--fit', $Fit,
        '--jinja',
        '--metrics',
        '--offline'
    )
    if ($UseSyclDevice) {
        $Arguments += @('--device', [string]$RuntimeLock.device)
    }

    Write-Host (
        "PROBE $Scenario model=$ModelAlias fit=$Fit gpu_layers=$GpuLayers " +
        "device=$(if ($UseSyclDevice) { [string]$RuntimeLock.device } else { 'CPU' })"
    )

    $PreviousSelector = $env:ONEAPI_DEVICE_SELECTOR
    $Process = $null
    $Started = [DateTimeOffset]::UtcNow
    try {
        $env:ONEAPI_DEVICE_SELECTOR = [string]$RuntimeLock.oneapi_device_selector
        $Process = Start-Process -FilePath $ServerBinary -ArgumentList $Arguments `
            -WorkingDirectory (Split-Path -Parent $ServerBinary) `
            -RedirectStandardOutput $StdoutPath `
            -RedirectStandardError $StderrPath `
            -WindowStyle Hidden -PassThru

        $Deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
        $Ready = $false
        do {
            if ($Process.HasExited) {
                break
            }
            try {
                $Models = Invoke-RestMethod -Method Get `
                    -Uri "http://127.0.0.1:$Port/v1/models" -TimeoutSec 2
                if ($Models.data) {
                    $Ready = $true
                    break
                }
            }
            catch {
                Start-Sleep -Milliseconds 500
            }
        } while ([DateTimeOffset]::UtcNow -lt $Deadline)

        if ($Ready) {
            $ElapsedMs = ([DateTimeOffset]::UtcNow - $Started).TotalMilliseconds
            Write-Host "OK  $Scenario charge le modèle en $([math]::Round($ElapsedMs, 1)) ms."
            return [pscustomobject]@{
                scenario = $Scenario
                fit = $Fit
                gpu_layers = $GpuLayers
                device = if ($UseSyclDevice) { [string]$RuntimeLock.device } else { 'CPU' }
                success = $true
                exit_code = $null
                wall_ms = [math]::Round($ElapsedMs, 1)
                stdout = $StdoutPath
                stderr = $StderrPath
                stderr_tail = Get-LogTailText -Path $StderrPath
            }
        }

        if (-not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            $Process.WaitForExit(10000)
            throw "Probe $Scenario non prêt après $TimeoutSeconds s."
        }

        $ElapsedMs = ([DateTimeOffset]::UtcNow - $Started).TotalMilliseconds
        $ExitCode = $Process.ExitCode
        $Tail = Get-LogTailText -Path $StderrPath
        Write-Warning "KO  $Scenario: llama-server exit=$ExitCode après $([math]::Round($ElapsedMs, 1)) ms."
        return [pscustomobject]@{
            scenario = $Scenario
            fit = $Fit
            gpu_layers = $GpuLayers
            device = if ($UseSyclDevice) { [string]$RuntimeLock.device } else { 'CPU' }
            success = $false
            exit_code = $ExitCode
            wall_ms = [math]::Round($ElapsedMs, 1)
            stdout = $StdoutPath
            stderr = $StderrPath
            stderr_tail = $Tail
        }
    }
    finally {
        if ($Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            $Process.WaitForExit(10000)
        }
        if ($null -eq $PreviousSelector) {
            Remove-Item Env:ONEAPI_DEVICE_SELECTOR -ErrorAction SilentlyContinue
        }
        else {
            $env:ONEAPI_DEVICE_SELECTOR = $PreviousSelector
        }
    }
}

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host '[DRY-RUN] Diagnostic direct d’un modèle llama.cpp sans passer par le routeur.'
    Write-Host "[DRY-RUN] Model=$Model Release=$($RuntimeLock.release) Device=$($RuntimeLock.device)"
    Write-Host '[DRY-RUN] Matrice: SYCL/all+fit on -> SYCL/all+fit off -> CPU/0+fit off.'
    Write-Host '[DRY-RUN] Chaque essai utilise un port loopback éphémère et capture stdout/stderr séparément.'
    Write-Host '[DRY-RUN] Aucun modèle n’est téléchargé et aucune configuration OpenClaw n’est modifiée.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
$RequiredModels = Get-RequiredOllamaModelList -RepoRoot $RepoRoot
$Matches = @($RequiredModels | Where-Object { $_ -ieq $Model })
if ($Matches.Count -ne 1) {
    throw "Modèle $Model absent de la flotte required: $($RequiredModels -join ', ')"
}
$ResolvedModel = [string]$Matches[0]
$ModelPath = Resolve-OllamaGgufPath -Model $ResolvedModel
$Binary = Get-IntelSyclServerBinary -VersionRoot $Paths.VersionRoot
if (-not $Binary) {
    throw 'Runtime Intel SYCL absent. Exécutez .\menu.ps1 -Action intel-sycl-setup.'
}
$Driver = Get-IntelArcB580DriverInfo
$DeviceEvidence = Test-IntelArcB580SyclDevice -ServerBinary $Binary -RuntimeLock $RuntimeLock
$ModelFile = Get-Item -LiteralPath $ModelPath
$ModelSha = (Get-FileHash -LiteralPath $ModelPath -Algorithm SHA256).Hash.ToLowerInvariant()

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$ProofDirectory = Join-Path $Paths.ProofRoot "direct-load-$Stamp"
New-Item -ItemType Directory -Path $ProofDirectory -Force | Out-Null

$Results = @()
$Results += Invoke-DirectIntelSyclLoadProbe `
    -ServerBinary $Binary -ModelPath $ModelPath -ModelAlias $ResolvedModel `
    -Scenario 'gpu_fit_on' -ProofDirectory $ProofDirectory -RuntimeLock $RuntimeLock `
    -Fit 'on' -GpuLayers 'all' -UseSyclDevice $true -TimeoutSeconds $TimeoutSeconds

if (-not [bool]$Results[-1].success) {
    $Results += Invoke-DirectIntelSyclLoadProbe `
        -ServerBinary $Binary -ModelPath $ModelPath -ModelAlias $ResolvedModel `
        -Scenario 'gpu_fit_off' -ProofDirectory $ProofDirectory -RuntimeLock $RuntimeLock `
        -Fit 'off' -GpuLayers 'all' -UseSyclDevice $true -TimeoutSeconds $TimeoutSeconds
}

if (-not [bool]$Results[-1].success) {
    $Results += Invoke-DirectIntelSyclLoadProbe `
        -ServerBinary $Binary -ModelPath $ModelPath -ModelAlias $ResolvedModel `
        -Scenario 'cpu_fit_off' -ProofDirectory $ProofDirectory -RuntimeLock $RuntimeLock `
        -Fit 'off' -GpuLayers '0' -UseSyclDevice $false -TimeoutSeconds $TimeoutSeconds
}

$ByScenario = @{}
foreach ($Result in $Results) {
    $ByScenario[[string]$Result.scenario] = $Result
}

$Diagnosis = if ($ByScenario['gpu_fit_on'] -and $ByScenario['gpu_fit_on'].success) {
    'router_only_or_transient'
}
elseif (
    $ByScenario['gpu_fit_off'] -and
    $ByScenario['gpu_fit_off'].success
) {
    'llama_fit_regression'
}
elseif (
    $ByScenario['cpu_fit_off'] -and
    $ByScenario['cpu_fit_off'].success
) {
    'sycl_offload_or_device_memory'
}
elseif ($ByScenario['cpu_fit_off']) {
    'gguf_or_llama_core_load'
}
else {
    'inconclusive'
}

$Proof = [ordered]@{
    schema_version = '1.0.0'
    diagnosed_at = [DateTimeOffset]::UtcNow.ToString('o')
    model = $ResolvedModel
    model_path = $ModelPath
    model_sha256 = $ModelSha
    model_size_bytes = [int64]$ModelFile.Length
    release = [string]$RuntimeLock.release
    release_commit = [string]$RuntimeLock.release_commit
    binary = $Binary
    binary_sha256 = (Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash.ToLowerInvariant()
    python = $ManagedPython
    driver = $Driver
    device = [string]$RuntimeLock.device
    oneapi_device_selector = [string]$RuntimeLock.oneapi_device_selector
    device_evidence = $DeviceEvidence
    context_tokens = [int]$RuntimeLock.context_tokens
    diagnosis = $Diagnosis
    probes = @($Results)
    openclaw_modified = $false
}
$ProofPath = Join-Path $ProofDirectory 'diagnostic.json'
$Proof | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ProofPath -Encoding utf8

Write-Host "INTEL_SYCL_MODEL_DIAGNOSTIC=$ProofPath"
Write-Host "DIAGNOSIS=$Diagnosis"
switch ($Diagnosis) {
    'router_only_or_transient' {
        Write-Host 'VERDICT=Le modèle charge directement avec les paramètres nominaux; le routeur/lifecycle reste la piste principale.'
    }
    'llama_fit_regression' {
        Write-Host 'VERDICT=Le modèle charge avec --fit off; le fitter llama.cpp est la cause isolée.'
    }
    'sycl_offload_or_device_memory' {
        Write-Host 'VERDICT=Le GGUF charge en CPU mais pas avec SYCL/all; la cause est dans l’offload SYCL ou la mémoire device.'
    }
    'gguf_or_llama_core_load' {
        Write-Host 'VERDICT=Le modèle échoue même en CPU-only avec ce build; inspecter stderr pour GGUF/tokenizer/architecture llama.cpp.'
    }
    default {
        Write-Host 'VERDICT=Diagnostic incomplet; inspecter les logs de probes.'
    }
}
exit 0
