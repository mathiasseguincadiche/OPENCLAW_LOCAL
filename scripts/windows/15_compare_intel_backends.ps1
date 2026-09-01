[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [ValidateRange(0, 7200)]
    [int]$HardTimeoutSeconds = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

function Write-CompareWatchdogProof {
    param(
        [Parameter(Mandatory)][string]$ProofRoot,
        [Parameter(Mandatory)][string]$Status,
        [Parameter(Mandatory)][string]$Mode,
        [Parameter(Mandatory)][int]$HardTimeout,
        [Parameter(Mandatory)][string]$Python,
        [Parameter(Mandatory)][string]$ChildStdout,
        [Parameter(Mandatory)][string]$ChildStderr,
        [Parameter(Mandatory)][string]$RouterStderr,
        [Parameter(Mandatory)][string]$RouterTail,
        [Parameter(Mandatory)][DateTimeOffset]$StartedAt,
        [Parameter(Mandatory)][int]$ProcessId,
        [AllowNull()][object]$ExitCode,
        [Parameter(Mandatory)][string]$Reason
    )

    New-Item -ItemType Directory -Path $ProofRoot -Force | Out-Null
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $ProofPath = Join-Path $ProofRoot "compare_watchdog_${Status}_${Stamp}.json"
    [ordered]@{
        schema_version = '1.0.0'
        status = $Status
        mode = $Mode
        started_at = $StartedAt.ToString('o')
        finished_at = [DateTimeOffset]::UtcNow.ToString('o')
        hard_timeout_seconds = $HardTimeout
        python = $Python
        process_id = $ProcessId
        exit_code = $ExitCode
        child_stdout = $ChildStdout
        child_stderr = $ChildStderr
        router_stderr = $RouterStderr
        router_stderr_tail = $RouterTail
        reason = $Reason
        gpu_released_by_router_stop = ($Status -eq 'timeout')
        promotion_allowed = $false
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ProofPath -Encoding utf8
    Write-Host "INTEL_SYCL_COMPARE_WATCHDOG_PROOF=$ProofPath"
    return $ProofPath
}

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
$CompareScript = Join-Path $RepoRoot 'scripts\28_compare_local_backends.py'
if ($HardTimeoutSeconds -gt 0 -and $HardTimeoutSeconds -lt 120) {
    throw 'HardTimeoutSeconds doit valoir 0 (automatique) ou être compris entre 120 et 7200 secondes.'
}
$EffectiveHardTimeout = if ($HardTimeoutSeconds -gt 0) {
    $HardTimeoutSeconds
}
elseif ($Quick) {
    420
}
else {
    1800
}
$ModeName = if ($Quick) { 'quick' } else { 'full' }

if ($DryRun) {
    $Mode = if ($Quick) { 'QUICK: 1 scénario, 1 répétition' } else { 'COMPLET: 2 scénarios, 2 répétitions' }
    Write-Host "[DRY-RUN] Comparaison B580 Ollama/Vulkan vs llama.cpp/SYCL — $Mode."
    Write-Host '[DRY-RUN] Utiliser le runtime Python géré OPENCLAW_LOCAL.'
    Write-Host '[DRY-RUN] Mêmes trois modèles, contexte 8192, température 0, Qwen thinking off pour comparabilité.'
    Write-Host '[DRY-RUN] Mesurer durée, chargement, prompt tok/s, decode tok/s et changements de modèle.'
    Write-Host "[DRY-RUN] Watchdog dur global=$EffectiveHardTimeout s; un blocage tue le benchmark et le routeur SYCL suivi."
    Write-Host '[DRY-RUN] Capturer stdout/stderr enfant et stderr llama-server pour diagnostic.'
    Write-Host '[DRY-RUN] Produire une preuve JSON watchdog en cas de timeout ou de sortie Python non nulle.'
    Write-Host '[DRY-RUN] Le résultat ne peut pas promouvoir automatiquement le backend.'
    exit 0
}

$ManagedPython = Enable-ClawLocalManagedPython -PlatformRoot $PlatformRoot
Write-Host "OK  Runtime Python géré: $ManagedPython"
$PythonIdentity = (& $ManagedPython -c 'import sys; print(sys.executable)' 2>&1 | Select-Object -Last 1).ToString().Trim()
if (-not $PythonIdentity) {
    throw 'Impossible de confirmer sys.executable pour le runtime Python géré.'
}
Write-Host "OK  Python benchmark effectif: $PythonIdentity"

try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
}
catch {
    throw "Ollama/Vulkan n'est pas disponible pour la comparaison: $($_.Exception.Message)"
}
try {
    $null = Wait-IntelSyclApi -BaseUrl ([string]$RuntimeLock.endpoint) -TimeoutSeconds 10
}
catch {
    throw 'Intel SYCL n''est pas prêt. Exécutez .\menu.ps1 -Action intel-sycl-setup.'
}

$Arguments = @('-u', $CompareScript)
if ($Quick) {
    $Arguments += @('--quick', '--repetitions', '1', '--timeout', '180')
}
else {
    $Arguments += @('--repetitions', '2', '--timeout', '300')
}

New-Item -ItemType Directory -Path $Paths.ProofRoot -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$ChildStdout = Join-Path $Paths.ProofRoot "compare_${Stamp}.stdout.log"
$ChildStderr = Join-Path $Paths.ProofRoot "compare_${Stamp}.stderr.log"
Remove-Item -LiteralPath $ChildStdout, $ChildStderr -Force -ErrorAction SilentlyContinue

$Process = $null
$PrintedStdout = 0
$PrintedStderr = 0
$StartedAt = [DateTimeOffset]::UtcNow
try {
    $Process = Start-Process -FilePath $ManagedPython -ArgumentList $Arguments `
        -WorkingDirectory $RepoRoot `
        -RedirectStandardOutput $ChildStdout `
        -RedirectStandardError $ChildStderr `
        -WindowStyle Hidden -PassThru
    Write-Host "OK  Watchdog benchmark PID=$($Process.Id) plafond=$EffectiveHardTimeout s."
    $Deadline = [DateTimeOffset]::UtcNow.AddSeconds($EffectiveHardTimeout)

    do {
        if (Test-Path -LiteralPath $ChildStdout) {
            $Lines = @(Get-Content -LiteralPath $ChildStdout)
            if ($Lines.Count -gt $PrintedStdout) {
                $Lines[$PrintedStdout..($Lines.Count - 1)] | ForEach-Object { Write-Host $_ }
                $PrintedStdout = $Lines.Count
            }
        }
        if (Test-Path -LiteralPath $ChildStderr) {
            $ErrorLines = @(Get-Content -LiteralPath $ChildStderr)
            if ($ErrorLines.Count -gt $PrintedStderr) {
                $ErrorLines[$PrintedStderr..($ErrorLines.Count - 1)] | ForEach-Object { Write-Host $_ }
                $PrintedStderr = $ErrorLines.Count
            }
        }
        if ($Process.HasExited) {
            break
        }
        Start-Sleep -Milliseconds 500
    } while ([DateTimeOffset]::UtcNow -lt $Deadline)

    if (-not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        $ExitedAfterStop = $Process.WaitForExit(10000)
        if (-not $ExitedAfterStop -and -not $Process.HasExited) {
            try {
                $Process.Kill($true)
            }
            catch {
                Write-Warning "Kill arbre Python impossible après timeout: $($_.Exception.Message)"
            }
            $null = $Process.WaitForExit(5000)
        }
        $TimeoutExitCode = if ($Process.HasExited) { $Process.ExitCode } else { $null }
        $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
        $RouterTail = if (Test-Path -LiteralPath $Paths.StderrLog) {
            (Get-Content -LiteralPath $Paths.StderrLog -Tail 160) -join "`n"
        }
        else {
            '<stderr llama-server absent>'
        }
        $Reason = "Benchmark dépassé après $EffectiveHardTimeout s; processus Python et routeur SYCL arrêtés."
        $null = Write-CompareWatchdogProof `
            -ProofRoot $Paths.ProofRoot -Status 'timeout' -Mode $ModeName `
            -HardTimeout $EffectiveHardTimeout -Python $PythonIdentity `
            -ChildStdout $ChildStdout -ChildStderr $ChildStderr `
            -RouterStderr $Paths.StderrLog -RouterTail $RouterTail `
            -StartedAt $StartedAt -ProcessId $Process.Id -ExitCode $TimeoutExitCode `
            -Reason $Reason
        throw (
            "Watchdog: benchmark interrompu après $EffectiveHardTimeout s. " +
            "Le routeur SYCL suivi a été arrêté pour libérer la B580.`n" +
            "STDOUT=$ChildStdout`nSTDERR=$ChildStderr`n" +
            "Dernières lignes llama-server:`n$RouterTail"
        )
    }

    $null = $Process.WaitForExit(10000)
    if (Test-Path -LiteralPath $ChildStdout) {
        $Lines = @(Get-Content -LiteralPath $ChildStdout)
        if ($Lines.Count -gt $PrintedStdout) {
            $Lines[$PrintedStdout..($Lines.Count - 1)] | ForEach-Object { Write-Host $_ }
        }
    }
    if (Test-Path -LiteralPath $ChildStderr) {
        $ErrorLines = @(Get-Content -LiteralPath $ChildStderr)
        if ($ErrorLines.Count -gt $PrintedStderr) {
            $ErrorLines[$PrintedStderr..($ErrorLines.Count - 1)] | ForEach-Object { Write-Host $_ }
        }
    }

    if ($Process.ExitCode -ne 0) {
        $RouterTail = if (Test-Path -LiteralPath $Paths.StderrLog) {
            (Get-Content -LiteralPath $Paths.StderrLog -Tail 120) -join "`n"
        }
        else {
            '<stderr llama-server absent>'
        }
        $Reason = "Comparateur Python terminé avec code $($Process.ExitCode)."
        $null = Write-CompareWatchdogProof `
            -ProofRoot $Paths.ProofRoot -Status 'failed' -Mode $ModeName `
            -HardTimeout $EffectiveHardTimeout -Python $PythonIdentity `
            -ChildStdout $ChildStdout -ChildStderr $ChildStderr `
            -RouterStderr $Paths.StderrLog -RouterTail $RouterTail `
            -StartedAt $StartedAt -ProcessId $Process.Id -ExitCode $Process.ExitCode `
            -Reason $Reason
        throw (
            "Comparaison Ollama/SYCL en échec (code $($Process.ExitCode)).`n" +
            "STDOUT=$ChildStdout`nSTDERR=$ChildStderr`n" +
            "Dernières lignes llama-server:`n$RouterTail"
        )
    }
}
finally {
    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        $null = $Process.WaitForExit(10000)
    }
}

Write-Host 'OK  Comparaison B580 terminée. Aucun backend n''a été promu automatiquement.'
exit 0
