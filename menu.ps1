[CmdletBinding()]
param(
    [ValidateSet(
        'menu', 'install-core', 'install-full', 'audit', 'configure-local', 'models',
        'configure-openclaw', 'deploy-agents', 'verify', 'benchmark', 'inventory',
        'e2e', 'qualification', 'intel-sycl-setup', 'intel-sycl-stop',
        'intel-sycl-verify', 'intel-sycl-compare', 'team', 'docs', 'logs'
    )]
    [string]$Action = 'menu',
    [switch]$DryRun,
    [switch]$Quick,
    [switch]$AllowRuntimeDrift,
    [ValidateSet('ollama-vulkan', 'llama-cpp-sycl')]
    [string]$Backend = 'ollama-vulkan',
    [switch]$NoLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$env:OPENCLAW_LOCAL_REPO_ROOT = $RepoRoot

$Scripts = @{
    'install-core' = Join-Path $RepoRoot 'scripts\windows\00_bootstrap.ps1'
    'install-full' = Join-Path $RepoRoot 'scripts\windows\11_install_full.ps1'
    audit = Join-Path $RepoRoot 'scripts\windows\01_audit_host.ps1'
    'configure-local' = Join-Path $RepoRoot 'scripts\windows\02_configure_local.ps1'
    models = Join-Path $RepoRoot 'scripts\windows\03_pull_models.ps1'
    'configure-openclaw' = Join-Path $RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
    'deploy-agents' = Join-Path $RepoRoot 'scripts\windows\09_deploy_agents.ps1'
    verify = Join-Path $RepoRoot 'scripts\windows\04_verify_local.ps1'
    benchmark = Join-Path $RepoRoot 'scripts\windows\05_benchmark.ps1'
    inventory = Join-Path $RepoRoot 'scripts\windows\06_collect_inventory.ps1'
    e2e = Join-Path $RepoRoot 'scripts\windows\10_test_openclaw_e2e.ps1'
    qualification = Join-Path $RepoRoot 'scripts\windows\07_run_qualification.ps1'
    'intel-sycl-setup' = Join-Path $RepoRoot 'scripts\windows\12_setup_intel_sycl.ps1'
    'intel-sycl-stop' = Join-Path $RepoRoot 'scripts\windows\13_stop_intel_sycl.ps1'
    'intel-sycl-verify' = Join-Path $RepoRoot 'scripts\windows\14_verify_intel_sycl.ps1'
    'intel-sycl-compare' = Join-Path $RepoRoot 'scripts\windows\15_compare_intel_backends.ps1'
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

function Get-LogsRoot {
    return (Join-Path (Get-PlatformRoot) 'proofs\logs')
}

function Write-ActionTranscriptStart {
    param([Parameter(Mandatory)][string]$Name)

    try {
        $LogsRoot = Get-LogsRoot
        New-Item -ItemType Directory -Path $LogsRoot -Force | Out-Null
        $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
        $SafeName = $Name -replace '[^a-zA-Z0-9._-]', '_'
        $LogPath = Join-Path $LogsRoot "${Stamp}_${SafeName}.log"
        Start-Transcript -Path $LogPath -UseMinimalHeader | Out-Null
        Write-Host "LOG=$LogPath"
        Write-Host "ACTION=$Name"
        Write-Host "STARTED_UTC=$([DateTimeOffset]::UtcNow.ToString('o'))"
        Write-Host "REPO_ROOT=$RepoRoot"
        Write-Host "PLATFORM_ROOT=$(Get-PlatformRoot)"
        return $LogPath
    }
    catch {
        Write-Warning "Journalisation automatique indisponible: $($_.Exception.Message)"
        return $null
    }
}

function Write-ActionTranscriptStop {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][ValidateSet('PASS', 'FAIL')][string]$Result
    )

    Write-Host "ACTION_RESULT=$Result"
    Write-Host "FINISHED_UTC=$([DateTimeOffset]::UtcNow.ToString('o'))"
    try {
        Stop-Transcript | Out-Null
    }
    catch {
        Write-Warning "Impossible d'arrêter proprement le transcript: $($_.Exception.Message)"
    }
    Write-Host "LOG_SAVED=$Path"
}

function Show-LogSummary {
    $LogsRoot = Get-LogsRoot
    Write-Host "LOG_ROOT=$LogsRoot"
    Write-Host "STRUCTURED_PROOFS=$(Join-Path (Get-PlatformRoot) 'proofs')"
    Write-Host "BENCHMARK_RESULTS=$(Join-Path $RepoRoot 'benchmarks\results')"

    if (-not (Test-Path -LiteralPath $LogsRoot)) {
        Write-Host 'Aucun transcript opérationnel enregistré.'
        return
    }

    $Logs = @(
        Get-ChildItem -LiteralPath $LogsRoot -Filter '*.log' -File |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 10
    )
    if ($Logs.Count -eq 0) {
        Write-Host 'Aucun transcript opérationnel enregistré.'
        return
    }

    $Logs |
        Select-Object LastWriteTime, Length, FullName |
        Format-Table -AutoSize
    Write-Host "LATEST_LOG=$($Logs[0].FullName)"
}

function Show-Title {
    Write-Host ''
    Write-Host '============================================================================== '
    Write-Host ' OPENCLAW_LOCAL — CENTRE DE CONTRÔLE LOCAL-FIRST WINDOWS 11 PRO'
    Write-Host '============================================================================== '
    Write-Host ' Nominal : OpenClaw + Ollama/Vulkan natifs Windows'
    Write-Host ' Intel   : llama.cpp/SYCL/Level Zero candidat B580, promotion explicite uniquement'
    Write-Host ' Cloud   : escalade explicite uniquement, jamais fallback silencieux'
}

function Invoke-Action {
    param(
        [Parameter(Mandatory)][string]$Name,
        [switch]$DryRunMode,
        [switch]$QuickMode,
        [switch]$AllowRuntimeDriftMode,
        [ValidateSet('ollama-vulkan', 'llama-cpp-sycl')]
        [string]$BackendMode = 'ollama-vulkan',
        [switch]$NoLogMode
    )

    if ($Name -eq 'docs') {
        Write-Host (Join-Path $RepoRoot 'docs\README.md')
        return
    }

    if ($Name -eq 'team') {
        Write-Host (Join-Path $RepoRoot 'agents')
        Write-Host (Join-Path $RepoRoot 'config\v1\model_routing.yaml')
        Write-Host (Join-Path $RepoRoot 'config\v1\tool_policy.yaml')
        return
    }

    if ($Name -eq 'logs') {
        Show-LogSummary
        return
    }

    $Script = $Scripts[$Name]
    if (-not (Test-Path -LiteralPath $Script)) {
        throw "Script introuvable pour l'action '$Name' : $Script"
    }

    $LogPath = $null
    $Result = 'FAIL'
    if (-not $DryRunMode -and -not $NoLogMode) {
        $LogPath = Write-ActionTranscriptStart -Name $Name
    }

    try {
        $global:LASTEXITCODE = 0
        if ($Name -in @('install-core', 'install-full')) {
            & $Script -DryRun:$DryRunMode -AllowRuntimeDrift:$AllowRuntimeDriftMode
        }
        elseif ($Name -in @('benchmark', 'qualification', 'intel-sycl-compare')) {
            & $Script -DryRun:$DryRunMode -Quick:$QuickMode
        }
        elseif ($Name -in @('configure-openclaw', 'e2e')) {
            & $Script -DryRun:$DryRunMode -Backend $BackendMode
        }
        else {
            & $Script -DryRun:$DryRunMode
        }
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            throw "Action '$Name' en échec (code $LASTEXITCODE)."
        }
        $Result = 'PASS'
    }
    finally {
        if ($LogPath) {
            Write-ActionTranscriptStop -Path $LogPath -Result $Result
        }
    }
}

if ($Action -ne 'menu') {
    Show-Title
    Invoke-Action -Name $Action -DryRunMode:$DryRun -QuickMode:$Quick `
        -AllowRuntimeDriftMode:$AllowRuntimeDrift -BackendMode $Backend -NoLogMode:$NoLog
    exit 0
}

while ($true) {
    Show-Title
    @'
1) Installation complète reproductible (runtime + modèles + OpenClaw + 8 agents + Gateway)
2) Installer/réparer uniquement le runtime verrouillé
3) Audit sans mutation
4) Configurer/vérifier Ollama local
5) Télécharger les modèles locaux de référence
6) Générer/appliquer la configuration OpenClaw (paramètre -Backend pour SYCL)
7) Déployer les 8 workspaces agents
8) Vérifier l'inférence locale Ollama
9) Lancer le benchmark (utiliser -Quick pour 8K uniquement)
10) Collecter l'inventaire de qualification
11) Tester OpenClaw E2E + tool-calling + réparation (paramètre -Backend pour SYCL)
12) Lancer la qualification matérielle (utiliser -Quick pour 36 cas au lieu de 72)
13) Afficher les contrats de l'équipe IA
14) Afficher la documentation
15) Afficher les derniers logs et preuves
16) Installer/démarrer Intel B580 llama.cpp SYCL/Level Zero
17) Vérifier Intel B580 SYCL + trois modèles
18) Comparer Ollama/Vulkan vs Intel SYCL (utiliser -Quick pour diagnostic court)
19) Arrêter le serveur Intel SYCL
0) Quitter
'@ | Write-Host

    switch (Read-Host 'Choix') {
        '1' { Invoke-Action -Name 'install-full' -DryRunMode:$DryRun -AllowRuntimeDriftMode:$AllowRuntimeDrift -BackendMode $Backend -NoLogMode:$NoLog }
        '2' { Invoke-Action -Name 'install-core' -DryRunMode:$DryRun -AllowRuntimeDriftMode:$AllowRuntimeDrift -BackendMode $Backend -NoLogMode:$NoLog }
        '3' { Invoke-Action -Name 'audit' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '4' { Invoke-Action -Name 'configure-local' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '5' { Invoke-Action -Name 'models' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '6' { Invoke-Action -Name 'configure-openclaw' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '7' { Invoke-Action -Name 'deploy-agents' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '8' { Invoke-Action -Name 'verify' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '9' { Invoke-Action -Name 'benchmark' -DryRunMode:$DryRun -QuickMode:$Quick -BackendMode $Backend -NoLogMode:$NoLog }
        '10' { Invoke-Action -Name 'inventory' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '11' { Invoke-Action -Name 'e2e' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '12' { Invoke-Action -Name 'qualification' -DryRunMode:$DryRun -QuickMode:$Quick -BackendMode $Backend -NoLogMode:$NoLog }
        '13' { Invoke-Action -Name 'team' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '14' { Invoke-Action -Name 'docs' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '15' { Invoke-Action -Name 'logs' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '16' { Invoke-Action -Name 'intel-sycl-setup' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '17' { Invoke-Action -Name 'intel-sycl-verify' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '18' { Invoke-Action -Name 'intel-sycl-compare' -DryRunMode:$DryRun -QuickMode:$Quick -BackendMode $Backend -NoLogMode:$NoLog }
        '19' { Invoke-Action -Name 'intel-sycl-stop' -DryRunMode:$DryRun -BackendMode $Backend -NoLogMode:$NoLog }
        '0' { exit 0 }
        default { Write-Warning 'Choix invalide.' }
    }

    Read-Host 'Entrée pour revenir au menu' | Out-Null
}
