[CmdletBinding()]
param(
    [ValidateSet('menu', 'audit', 'configure-local', 'models', 'verify', 'benchmark', 'inventory', 'qualification', 'team', 'docs')]
    [string]$Action = 'menu',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

$Scripts = @{
    audit = Join-Path $RepoRoot 'scripts\windows\01_audit_host.ps1'
    'configure-local' = Join-Path $RepoRoot 'scripts\windows\02_configure_local.ps1'
    models = Join-Path $RepoRoot 'scripts\windows\03_pull_models.ps1'
    verify = Join-Path $RepoRoot 'scripts\windows\04_verify_local.ps1'
    benchmark = Join-Path $RepoRoot 'scripts\windows\05_benchmark.ps1'
    inventory = Join-Path $RepoRoot 'scripts\windows\06_collect_inventory.ps1'
    qualification = Join-Path $RepoRoot 'scripts\windows\07_run_qualification.ps1'
}

function Show-Title {
    Write-Host ''
    Write-Host '============================================================================== '
    Write-Host ' OPENCLAW_LOCAL — CENTRE DE CONTRÔLE LOCAL-FIRST WINDOWS 11 PRO'
    Write-Host '============================================================================== '
    Write-Host ' Nominal : OpenClaw + Ollama natifs Windows'
    Write-Host ' Cloud   : escalade optionnelle, jamais fallback silencieux'
}

function Invoke-Action {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [switch]$DryRunMode
    )

    if ($Name -eq 'docs') {
        Write-Host (Join-Path $RepoRoot 'docs\README.md')
        return
    }

    if ($Name -eq 'team') {
        Write-Host (Join-Path $RepoRoot 'agents')
        Write-Host (Join-Path $RepoRoot 'config\v1\model_routing.yaml')
        return
    }

    $Script = $Scripts[$Name]
    if (-not (Test-Path -LiteralPath $Script)) {
        throw "Script introuvable pour l'action '$Name' : $Script"
    }

    & $Script -DryRun:$DryRunMode
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Action '$Name' en échec (code $LASTEXITCODE)."
    }
}

if ($Action -ne 'menu') {
    Show-Title
    Invoke-Action -Name $Action -DryRunMode:$DryRun
    exit 0
}

while ($true) {
    Show-Title
    @'
1) Audit sans mutation
2) Configurer/vérifier Ollama local
3) Télécharger les modèles locaux de référence
4) Vérifier l'inférence locale
5) Lancer le benchmark simple
6) Collecter l'inventaire de qualification
7) Lancer la qualification matérielle complète
8) Afficher les contrats de l'équipe IA
9) Afficher la documentation
0) Quitter
'@ | Write-Host

    switch (Read-Host 'Choix') {
        '1' { Invoke-Action -Name 'audit' -DryRunMode:$DryRun }
        '2' { Invoke-Action -Name 'configure-local' -DryRunMode:$DryRun }
        '3' { Invoke-Action -Name 'models' -DryRunMode:$DryRun }
        '4' { Invoke-Action -Name 'verify' -DryRunMode:$DryRun }
        '5' { Invoke-Action -Name 'benchmark' -DryRunMode:$DryRun }
        '6' { Invoke-Action -Name 'inventory' -DryRunMode:$DryRun }
        '7' { Invoke-Action -Name 'qualification' -DryRunMode:$DryRun }
        '8' { Invoke-Action -Name 'team' -DryRunMode:$DryRun }
        '9' { Invoke-Action -Name 'docs' -DryRunMode:$DryRun }
        '0' { exit 0 }
        default { Write-Warning 'Choix invalide.' }
    }

    Read-Host 'Entrée pour revenir au menu' | Out-Null
}
