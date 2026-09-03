[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ResultsDir = Join-Path $RepoRoot 'benchmarks\results'
$RuntimeLockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
$RuntimeLock = Get-Content -Raw -LiteralPath $RuntimeLockPath | ConvertFrom-Json
$HardwareInventory = Join-Path $PSScriptRoot 'lib\hardware_inventory.ps1'
. $HardwareInventory

if ($DryRun) {
    Write-Host '[DRY-RUN] Collecter OS, CPU, RAM, GPU/pilotes et versions runtime.'
    Write-Host '[DRY-RUN] Résoudre la VRAM via HardwareInformation.qwMemorySize; les sources 32 bits restent informatives.'
    Write-Host '[DRY-RUN] Comparer les versions observées au runtime lock versionné.'
    Write-Host "[DRY-RUN] Écrire l'inventaire dans $ResultsDir sans secret."
    exit 0
}

function Get-NativeVersion([string]$Command, [string[]]$Arguments) {
    $Candidate = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $Candidate) {
        return $null
    }
    try {
        return ((& $Candidate.Source @Arguments 2>&1 | Out-String).Trim())
    }
    catch {
        return $null
    }
}

function Get-ManagedVersion([string]$Path, [string[]]$Arguments) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    try {
        return ((& $Path @Arguments 2>&1 | Out-String).Trim())
    }
    catch {
        return $null
    }
}

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$Os = Get-CimInstance Win32_OperatingSystem
$Cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$Computer = Get-CimInstance Win32_ComputerSystem
$Gpu = @(Get-OpenClawGpuInventory)
$OllamaModels = @()
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    $OllamaModels = @((& ollama list 2>$null | Select-Object -Skip 1) -join "`n")
}

$PlatformRoot = Get-PlatformRoot
$ManagedNode = Join-Path $PlatformRoot 'runtime\node\node.exe'
$ManagedPython = Join-Path $PlatformRoot 'runtime\venv\Scripts\python.exe'
$ManagedOpenClaw = Join-Path $PlatformRoot 'runtime\npm-global\openclaw.cmd'
$OpenClawConfig = Join-Path $PlatformRoot 'state\openclaw.json'
$AgentMarkerCount = @(
    Get-ChildItem -Path (Join-Path $PlatformRoot 'workspaces') `
        -Filter '.openclaw-local-managed' -Recurse -ErrorAction SilentlyContinue
).Count

$Payload = [ordered]@{
    schema_version = '1.1.0'
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
    platform_root = $PlatformRoot
    runtime_expected = [ordered]@{
        powershell_minimum_major = $RuntimeLock.powershell.minimum_major
        python_preferred = $RuntimeLock.python.preferred
        node_preferred = $RuntimeLock.node.preferred
        openclaw_preferred = $RuntimeLock.openclaw.preferred
        ollama_preferred = $RuntimeLock.ollama.preferred
    }
    runtime_observed = [ordered]@{
        powershell = $PSVersionTable.PSVersion.ToString()
        python_managed = Get-ManagedVersion $ManagedPython @('--version')
        node_managed = Get-ManagedVersion $ManagedNode @('--version')
        ollama = Get-NativeVersion 'ollama' @('--version')
        openclaw_managed = Get-ManagedVersion $ManagedOpenClaw @('--version')
        openclaw_path = Get-NativeVersion 'openclaw' @('--version')
    }
    openclaw = [ordered]@{
        config_present = Test-Path -LiteralPath $OpenClawConfig
        managed_agent_markers = $AgentMarkerCount
        expected_agents = 8
    }
    ollama_models_text = $OllamaModels
    notes = @(
        'Inventaire de qualification; aucune performance n est déduite de cet inventaire.',
        'La VRAM fiable utilise HardwareInformation.qwMemorySize 64 bits du registre Windows lorsque disponible.',
        'HardwareInformation.MemorySize et AdapterRAM sont conservés uniquement comme données informatives 32 bits.',
        'Une version observée différente du runtime lock impose une nouvelle qualification.'
    )
}

$Path = Join-Path $ResultsDir ("inventory_{0}.json" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$Payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding utf8NoBOM
Write-Host "EVIDENCE=$Path"
exit 0
