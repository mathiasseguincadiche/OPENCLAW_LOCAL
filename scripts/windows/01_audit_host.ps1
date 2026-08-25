[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

$Gpu = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
    Select-Object -First 4 Name, AdapterRAM, DriverVersion
if ($Gpu) {
    Write-Host 'GPU détecté :'
    $Gpu | Format-Table -AutoSize
}

$OllamaReachable = $false
try {
    $null = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    $OllamaReachable = $true
} catch {
    $OllamaReachable = $false
}
Write-Host "Ollama API : $(if ($OllamaReachable) { 'OK loopback' } else { 'INDISPONIBLE' })"

if ($DryRun) {
    Write-Host '[DRY-RUN] Audit uniquement : aucune mutation prévue.'
}
