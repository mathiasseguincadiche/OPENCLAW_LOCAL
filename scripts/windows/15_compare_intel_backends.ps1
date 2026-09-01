[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Quick,
    [ValidateRange(120, 7200)]
    [int]$HardTimeoutSeconds = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')
. (Join-Path $PSScriptRoot 'lib\python_runtime.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock
$CompareScript = Join-Path $RepoRoot 'scripts\28_compare_local_backends.py'
$EffectiveHardTimeout = if ($HardTimeoutSeconds -gt 0) {
    $HardTimeoutSeconds
}
elseif ($Quick) {
    420
}
else {
    1800
}

if ($DryRun) {
    $Mode = if ($Quick) { 'QUICK: 1 scénario, 1 répétition' } else { 'COMPLET: 2 scénarios, 2 répétitions' }
    Write-Host "[DRY-RUN] Comparaison B580 Ollama/Vulkan vs llama.cpp/SYCL — $Mode."
    Write-Host '[DRY-RUN] Utiliser le runtime Python géré OPENCLAW_LOCAL.'
    Write-Host '[DRY-RUN] Mêmes trois modèles, contexte 8192, température 0, Qwen thinking off pour comparabilité.'
    Write-Host '[DRY-RUN] Mesurer durée, chargement, prompt tok/s, decode tok/s et changements de modèle.'
    Write-Host "[DRY-RUN] Watchdog dur global=$EffectiveHardTimeout s; un blocage tue le benchmark et le routeur SYCL suivi."
    Write-Host '[DRY-RUN] Capturer stdout/stderr enfant et stderr llama-server pour diagnostic.'
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
        $null = $Process.WaitForExit(10000)
        $null = Stop-IntelSyclServer -StatePath $Paths.ProcessState -Confirm:$false
        $RouterTail = if (Test-Path -LiteralPath $Paths.StderrLog) {
            (Get-Content -LiteralPath $Paths.StderrLog -Tail 160) -join "`n"
        }
        else {
            '<stderr llama-server absent>'
        }
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
