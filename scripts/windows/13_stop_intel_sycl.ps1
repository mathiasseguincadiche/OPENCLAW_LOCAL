[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_sycl.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelSyclRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelSyclPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host "[DRY-RUN] Arrêter le serveur Intel SYCL suivi par $($Paths.ProcessState)."
    Write-Host '[DRY-RUN] Aucun changement de configuration OpenClaw.'
    exit 0
}

Stop-IntelSyclServer -StatePath $Paths.ProcessState
Write-Host 'OK  Backend Intel SYCL arrêté. La configuration OpenClaw existante n''est pas modifiée.'
exit 0
