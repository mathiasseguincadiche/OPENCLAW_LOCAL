[CmdletBinding()]
param(
    [ValidateSet(
        'menu', 'install-core', 'install-full', 'audit', 'configure-local', 'models',
        'configure-openclaw', 'deploy-agents', 'verify', 'benchmark', 'inventory',
        'e2e', 'qualification', 'team', 'docs'
    )]
    [string]$Action = 'menu',
    [switch]$DryRun,
    [switch]$AllowRuntimeDrift
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

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
}

function Show-Title {
    Write-Host ''
    Write-Host '============================================================================== '
    Write-Host ' OPENCLAW_LOCAL — CENTRE DE CONTRÔLE LOCAL-FIRST WINDOWS 11 PRO'
    Write-Host '============================================================================== '
    Write-Host ' Nominal : OpenClaw + Ollama natifs Windows'
    Write-Host ' Cloud   : escalade explicite uniquement, jamais fallback silencieux'
}

function Invoke-Action {
    param(
        [Parameter(Mandatory)][string]$Name,
        [switch]$DryRunMode,
        [switch]$AllowRuntimeDriftMode
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

    $Script = $Scripts[$Name]
    if (-not (Test-Path -LiteralPath $Script)) {
        throw "Script introuvable pour l'action '$Name' : $Script"
    }

    if ($Name -in @('install-core', 'install-full')) {
        & $Script -DryRun:$DryRunMode -AllowRuntimeDrift:$AllowRuntimeDriftMode
    }
    else {
        & $Script -DryRun:$DryRunMode
    }
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Action '$Name' en échec (code $LASTEXITCODE)."
    }
}

if ($Action -ne 'menu') {
    Show-Title
    Invoke-Action -Name $Action -DryRunMode:$DryRun -AllowRuntimeDriftMode:$AllowRuntimeDrift
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
6) Générer/appliquer la configuration OpenClaw
7) Déployer les 8 workspaces agents
8) Vérifier l'inférence locale Ollama
9) Lancer le benchmark simple
10) Collecter l'inventaire de qualification
11) Tester OpenClaw E2E + tool-calling + réparation
12) Lancer la qualification matérielle complète
13) Afficher les contrats de l'équipe IA
14) Afficher la documentation
0) Quitter
'@ | Write-Host

    switch (Read-Host 'Choix') {
        '1' { Invoke-Action -Name 'install-full' -DryRunMode:$DryRun -AllowRuntimeDriftMode:$AllowRuntimeDrift }
        '2' { Invoke-Action -Name 'install-core' -DryRunMode:$DryRun -AllowRuntimeDriftMode:$AllowRuntimeDrift }
        '3' { Invoke-Action -Name 'audit' -DryRunMode:$DryRun }
        '4' { Invoke-Action -Name 'configure-local' -DryRunMode:$DryRun }
        '5' { Invoke-Action -Name 'models' -DryRunMode:$DryRun }
        '6' { Invoke-Action -Name 'configure-openclaw' -DryRunMode:$DryRun }
        '7' { Invoke-Action -Name 'deploy-agents' -DryRunMode:$DryRun }
        '8' { Invoke-Action -Name 'verify' -DryRunMode:$DryRun }
        '9' { Invoke-Action -Name 'benchmark' -DryRunMode:$DryRun }
        '10' { Invoke-Action -Name 'inventory' -DryRunMode:$DryRun }
        '11' { Invoke-Action -Name 'e2e' -DryRunMode:$DryRun }
        '12' { Invoke-Action -Name 'qualification' -DryRunMode:$DryRun }
        '13' { Invoke-Action -Name 'team' -DryRunMode:$DryRun }
        '14' { Invoke-Action -Name 'docs' -DryRunMode:$DryRun }
        '0' { exit 0 }
        default { Write-Warning 'Choix invalide.' }
    }

    Read-Host 'Entrée pour revenir au menu' | Out-Null
}
