[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'lib\intel_vulkan.ps1')

$PlatformRoot = Get-OpenClawLocalPlatformRoot
$RuntimeLock = Get-IntelVulkanRuntimeLock -RepoRoot $RepoRoot
$Paths = Get-IntelVulkanPathSet -PlatformRoot $PlatformRoot -RuntimeLock $RuntimeLock

if ($DryRun) {
    Write-Host "[DRY-RUN] Arrêter le routeur Intel Vulkan suivi: $($Paths.ProcessState)"
    exit 0
}

$null = Stop-IntelVulkanServer -StatePath $Paths.ProcessState -Confirm:$false
Write-Host 'OK  Backend Intel Vulkan arrêté.'
exit 0
