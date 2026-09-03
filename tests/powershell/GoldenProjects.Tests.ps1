Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Golden projects pre-V1 operator path' {
    It 'expose une action golden dans le menu avec le contrat 30 cas actuel' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Menu = Get-Content -Raw -LiteralPath (Join-Path $TestRepoRoot 'menu.ps1')

        $Menu | Should -Match "'golden'"
        $Menu | Should -Match '21_run_golden_projects\.ps1'
        $Menu | Should -Match '30 cas HARD-40M'
        $Menu | Should -Match 'reset \+ prepare \+ execute \+ evaluate'
        $Menu | Should -Not -Match '36 cas au lieu de 72'
    }

    It 'utilise le Python gere pour les cinq golden projects' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Runner = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\21_run_golden_projects.ps1'
        )

        $Runner | Should -Match 'python_runtime\.ps1'
        $Runner | Should -Match 'Enable-ClawLocalManagedPython'
        $Runner | Should -Match '& \$ManagedPython'
        $Runner | Should -Match '--scenario all --prepare --reset --execute --evaluate'
        $Runner | Should -Not -Match '&\s+python(?:\.exe)?\b'
    }

    It 'auto-active le venv gere dans le runner Python direct apres resolution de root' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Runner = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\49_run_golden_projects.py'
        )

        $Runner | Should -Match 'requested_root'
        $Runner | Should -Match 'parse_known_args'
        $Runner | Should -Match '_activate_repository_runtime\(platform_root\)'
        $Runner | Should -Match 'runtime.*venv.*Scripts.*python\.exe'
        $Runner | Should -Match 'os\.execv'
        $Runner | Should -Match 'sys\.executable'
    }

    It 'offre un DryRun golden sans lancer de modele' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
            -Action golden -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match 'Golden projects pré-V1'
        $Text | Should -Match '5 scénarios'
        $Text | Should -Match 'Python géré OPENCLAW_LOCAL'
    }
}
