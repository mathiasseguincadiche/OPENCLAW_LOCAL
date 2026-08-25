[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ResultsDir = Join-Path $RepoRoot 'benchmarks\results'

if ($DryRun) {
    Write-Host "[DRY-RUN] Collecter OS, CPU, RAM, GPU/pilotes, PowerShell, Ollama et OpenClaw."
    Write-Host "[DRY-RUN] Écrire l'inventaire dans $ResultsDir sans secret."
    exit 0
}

function Get-NativeVersion([string]$Command, [string[]]$Arguments) {
    $candidate = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $candidate) { return $null }
    try {
        return ((& $candidate.Source @Arguments 2>&1 | Out-String).Trim())
    } catch {
        return $null
    }
}

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$Os = Get-CimInstance Win32_OperatingSystem
$Cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$Computer = Get-CimInstance Win32_ComputerSystem
$Gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM)
$OllamaModels = @()
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    $OllamaModels = @((& ollama list 2>$null | Select-Object -Skip 1) -join "`n")
}

$Payload = [ordered]@{
    schema_version = '1.0.0'
    generated_at = [DateTimeOffset]::UtcNow.ToString('o')
    os = [ordered]@{
        caption = $Os.Caption
        version = $Os.Version
        build = $Os.BuildNumber
        architecture = $Os.OSArchitecture
    }
    cpu = [ordered]@{
        name = $Cpu.Name
        cores = $Cpu.NumberOfCores
        logical_processors = $Cpu.NumberOfLogicalProcessors
    }
    system_memory_gb = [math]::Round($Computer.TotalPhysicalMemory / 1GB, 2)
    gpu = $Gpu
    powershell = $PSVersionTable.PSVersion.ToString()
    ollama_version = Get-NativeVersion 'ollama' @('--version')
    openclaw_version = Get-NativeVersion 'openclaw' @('--version')
    ollama_models_text = $OllamaModels
    notes = @(
        'Inventaire de qualification; aucune métrique de performance n est déduite de cet inventaire.',
        'AdapterRAM de Win32_VideoController peut être imprécis; la VRAM de référence reste contractuelle.'
    )
}

$Path = Join-Path $ResultsDir ("inventory_{0}.json" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$Payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding utf8NoBOM
Write-Host "EVIDENCE=$Path"
exit 0
