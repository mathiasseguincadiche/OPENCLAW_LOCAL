Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Ministral Reasoning vs Granite local model challenger' {
    It 'expose un parcours DryRun sans promotion automatique' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Join-Path $TestRepoRoot 'scripts\windows\23_compare_model_challenger.ps1'

        $Output = & pwsh -NoLogo -NoProfile -File $Script -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match '(?i)DRY-RUN'
        $Text | Should -Match 'Ministral-3-14B-Reasoning-2512-GGUF:Q4_K_M'
        $Text | Should -Match 'granite4\.2:8b-q4_K_M'
        $Text | Should -Match 'tool-calling natif'
        $Text | Should -Match 'Aucune promotion automatique'
    }

    It 'utilise le Python géré et le runner versionné' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\23_compare_model_challenger.ps1'
        )

        $Script | Should -Match 'python_runtime\.ps1'
        $Script | Should -Match 'Enable-ClawLocalManagedPython'
        $Script | Should -Match '52_compare_tool_calling_models\.py'
        $Script | Should -Match 'PROMOTION|promotion'
    }

    It 'conserve Granite hors de la flotte routée' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Catalog = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\model_catalog.yaml'
        )
        $Policy = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\qualification_policy.yaml'
        )

        $Catalog | Should -Match 'benchmark_challengers:'
        $Catalog | Should -Match 'granite-devops:'
        $Catalog | Should -Match 'routing_active:\s*false'
        $Catalog | Should -Match 'local_only:\s*true'
        $Policy | Should -Match 'benchmark_challengers_count_as_routed_models:\s*false'
        $Policy | Should -Match 'human_decision_required:\s*true'
        $Policy | Should -Match 'cloud_models_supported:\s*false'
    }
}
