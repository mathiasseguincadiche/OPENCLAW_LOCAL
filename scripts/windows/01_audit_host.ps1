[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$HardwareInventory = Join-Path $PSScriptRoot 'lib\hardware_inventory.ps1'
. $HardwareInventory

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

Write-Host '=== Audit OPENCLAW_LOCAL ==='
Write-Host "OS         : $([System.Environment]::OSVersion.VersionString)"
Write-Host "PowerShell : $($PSVersionTable.PSVersion)"

$IsWindowsHost = $IsWindows
Write-Host "Windows    : $IsWindowsHost"

foreach ($Command in @('python', 'openclaw', 'ollama')) {
    $Present = Test-Command $Command
    Write-Host ("{0,-10} : {1}" -f $Command, $(if ($Present) { 'OK' } else { 'ABSENT' }))
}

$Gpu = @(Get-OpenClawGpuInventory)
if ($Gpu.Count -gt 0) {
    Write-Host 'GPU détecté :'
    foreach ($Adapter in $Gpu) {
        Write-Host "  $($Adapter.name)"
        Write-Host "    Pilote : $($Adapter.driver_version)"
        if ($Adapter.vram_reliable) {
            Write-Host "    VRAM   : $($Adapter.vram_gib) GiB (source fiable: registre Windows)"
        }
        elseif ($null -ne $Adapter.cim_adapter_ram_gib) {
            Write-Host (
                "    VRAM   : non déterminée de façon fiable " +
                "(CIM rapporte $($Adapter.cim_adapter_ram_gib) GiB, informatif uniquement)"
            )
        }
        else {
            Write-Host '    VRAM   : non déterminée de façon fiable'
        }
    }
}

$OllamaReachable = $false
try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    $OllamaReachable = $true
}
catch {
    $OllamaReachable = $false
}
Write-Host "Ollama API : $(if ($OllamaReachable) { 'OK loopback' } else { 'INDISPONIBLE' })"

if ($DryRun) {
    Write-Host '[DRY-RUN] Audit uniquement : aucune mutation prévue.'
}
