[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$AgentsRoot = Join-Path $RepoRoot 'agents'
$SharedRoot = Join-Path $AgentsRoot '_shared'
$AgentIds = @(
    'chef-operations',
    'expert-recherche',
    'architecte-solutions',
    'ingenieur-devops',
    'ingenieur-securite',
    'ingenieur-release-forges',
    'redacteur-technique',
    'auditeur-qualite'
)

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

$PlatformRoot = Get-PlatformRoot
$WorkspacesRoot = Join-Path $PlatformRoot 'workspaces'
$Contract = Get-Content -Raw -LiteralPath (Join-Path $SharedRoot 'CONTRACT.md')
$Pedagogy = Get-Content -Raw -LiteralPath (Join-Path $SharedRoot 'PEDAGOGY.md')
$Tools = Get-Content -Raw -LiteralPath (Join-Path $SharedRoot 'TOOLS.md')
$Heartbeat = Get-Content -Raw -LiteralPath (Join-Path $SharedRoot 'HEARTBEAT.md')
$UserTemplate = @'
# Utilisateur

Ce workspace est public et reproductible. Aucune donnée personnelle, secret, préférence privée ou mémoire utilisateur ne doit être ajoutée ici automatiquement.

Les informations propres à l'opérateur restent dans l'état runtime local non versionné.
'@

foreach ($AgentId in $AgentIds) {
    $Source = Join-Path $AgentsRoot $AgentId
    $Workspace = Join-Path $WorkspacesRoot $AgentId
    $Marker = Join-Path $Workspace '.openclaw-local-managed'

    foreach ($Required in @('AGENTS.md', 'SOUL.md', 'IDENTITY.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Source $Required))) {
            throw "Source agent incomplète: $AgentId/$Required"
        }
    }

    if ((Test-Path -LiteralPath $Workspace) -and -not (Test-Path -LiteralPath $Marker)) {
        throw "Workspace non géré déjà présent: $Workspace. Refus d'écrasement."
    }

    if ($DryRun) {
        Write-Host "[DRY-RUN] Déployer $AgentId -> $Workspace avec contrat pédagogique transversal"
        continue
    }

    New-Item -ItemType Directory -Path $Workspace -Force | Out-Null
    $RoleAgents = Get-Content -Raw -LiteralPath (Join-Path $Source 'AGENTS.md')
    $MergedAgents = @"
# Contrat global OPENCLAW_LOCAL

$Contract

---

# Contrat pédagogique transversal obligatoire

$Pedagogy

---

# Contrat spécifique du rôle

$RoleAgents
"@
    Set-Content -LiteralPath (Join-Path $Workspace 'AGENTS.md') -Value $MergedAgents -Encoding utf8
    Copy-Item -LiteralPath (Join-Path $Source 'SOUL.md') -Destination (Join-Path $Workspace 'SOUL.md') -Force
    Copy-Item -LiteralPath (Join-Path $Source 'IDENTITY.md') -Destination (Join-Path $Workspace 'IDENTITY.md') -Force
    Set-Content -LiteralPath (Join-Path $Workspace 'TOOLS.md') -Value $Tools -Encoding utf8
    Set-Content -LiteralPath (Join-Path $Workspace 'HEARTBEAT.md') -Value $Heartbeat -Encoding utf8
    Set-Content -LiteralPath (Join-Path $Workspace 'USER.md') -Value $UserTemplate -Encoding utf8
    Set-Content -LiteralPath $Marker -Value "managed_by=OPENCLAW_LOCAL`nagent=$AgentId" -Encoding utf8
    Write-Host "OK  $AgentId déployé avec pédagogie transversale."
}

exit 0
