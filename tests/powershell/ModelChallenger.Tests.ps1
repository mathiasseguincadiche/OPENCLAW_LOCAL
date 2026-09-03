Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Gemma vs Ministral model challenger' {
    It 'expose un parcours DryRun sans promotion automatique' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Join-Path $TestRepoRoot 'scripts\windows\23_compare_model_challenger.ps1'

        $Output = & pwsh -NoLogo -NoProfile -File $Script -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match '(?i)DRY-RUN'
        $Text | Should -Match 'gemma3:12b-it-q4_K_M'
        $Text | Should -Match 'ministral-3:14b-instruct-2512-q4_K_M'
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

    It 'conserve Ministral hors de la flotte routée' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Catalog = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\model_catalog.yaml'
        )
        $Policy = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\qualification_policy.yaml'
        )

        $Catalog | Should -Match 'benchmark_challengers:'
        $Catalog | Should -Match 'ministral-tool-calling:'
        $Catalog | Should -Match 'routing_active:\s*false'
        $Policy | Should -Match 'benchmark_challengers_count_as_routed_models:\s*false'
        $Policy | Should -Match 'human_decision_required:\s*true'
    }
}
