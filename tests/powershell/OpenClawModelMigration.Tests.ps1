Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Migration de flotte OpenClaw' {
    BeforeAll {
        $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:Configure = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
        )
    }

    It 'utilise --replace-path pour les chemins gérés du patch' {
        ($script:Configure.Split("'--replace-path', 'models.providers'").Count - 1) |
            Should -Be 2
        ($script:Configure.Split("'--replace-path', 'agents.list'").Count - 1) |
            Should -Be 2
    }

    It 'n utilise jamais le flag --replace de config set sur config patch' {
        $script:Configure | Should -Not -Match "'--replace'"
    }

    It 'valide le patch avant de l appliquer' {
        $DryRunIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath, '--dry-run',"
        )
        $ApplyIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath,"
        )
        $SecondApplyIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath,",
            $DryRunIndex + 1
        )
        $DryRunIndex | Should -BeGreaterThan -1
        $ApplyIndex | Should -Be $DryRunIndex
        $SecondApplyIndex | Should -BeGreaterThan $DryRunIndex
    }

    It 'rend le remplacement explicite dans le dry-run pour l''opérateur' {
        $script:Configure | Should -Match 'Migration gérée:'
        $script:Configure | Should -Match 'retirer les anciens providers et IDs'
        $script:Configure | Should -Match 'models\.providers'
        $script:Configure | Should -Match 'agents\.list'
        $script:Configure | Should -Match '--replace-path'
    }
}
