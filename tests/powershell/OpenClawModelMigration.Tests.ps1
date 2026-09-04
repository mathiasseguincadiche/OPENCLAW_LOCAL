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
        $ProvidersPattern = [regex]::Escape("'--replace-path', 'models.providers'")
        $AgentsPattern = [regex]::Escape("'--replace-path', 'agents.list'")
        [regex]::Matches($script:Configure, $ProvidersPattern).Count | Should -Be 2
        [regex]::Matches($script:Configure, $AgentsPattern).Count | Should -Be 2
    }

    It 'n utilise jamais le flag --replace de config set sur config patch' {
        $script:Configure | Should -Not -Match "'--replace'"
    }

    It 'valide le patch avant de l appliquer' {
        $DryRunIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath, '--dry-run',"
        )
        $FirstPatchIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath,"
        )
        $ApplyIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath,",
            $DryRunIndex + 1
        )
        $DryRunIndex | Should -BeGreaterThan -1
        $FirstPatchIndex | Should -Be $DryRunIndex
        $ApplyIndex | Should -BeGreaterThan $DryRunIndex
    }

    It 'rend le remplacement explicite dans le dry-run pour l''opérateur' {
        $script:Configure | Should -Match 'Migration gérée:'
        $script:Configure | Should -Match 'retirer les anciens providers et IDs'
        $script:Configure | Should -Match 'models\.providers'
        $script:Configure | Should -Match 'agents\.list'
        $script:Configure | Should -Match '--replace-path'
    }
}
