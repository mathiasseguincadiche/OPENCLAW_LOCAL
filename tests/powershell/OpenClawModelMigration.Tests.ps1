Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Migration de flotte OpenClaw' {
    BeforeAll {
        $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:Configure = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
        )
    }

    It 'valide le patch avec --replace pour retirer les anciens IDs gérés' {
        $script:Configure | Should -Match [regex]::Escape(
            "'config', 'patch', '--file', `$PatchPath, '--dry-run', '--replace'"
        )
    }

    It 'applique le patch avec --replace après le dry-run' {
        $DryRunIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath, '--dry-run', '--replace'"
        )
        $ApplyIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath, '--replace'"
        )
        $DryRunIndex | Should -BeGreaterThan -1
        $ApplyIndex | Should -BeGreaterThan -1
        $DryRunIndex | Should -BeLessThan $ApplyIndex
    }

    It 'rend le remplacement explicite dans le DryRun opérateur' {
        $script:Configure | Should -Match 'Migration gérée:'
        $script:Configure | Should -Match 'retirer les anciens IDs'
        $script:Configure | Should -Match 'models\.providers\.\*\.models'
        $script:Configure | Should -Match 'agents\.list'
    }
}
