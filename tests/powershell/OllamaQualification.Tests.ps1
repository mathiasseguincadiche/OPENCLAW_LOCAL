Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Qualification Ollama lisible et bornée' {
    It 'utilise l API locale pour le smoke test et non ollama run' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Verify = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\04_verify_local.ps1'
        )
        $Verify | Should -Match '/api/generate'
        $Verify | Should -Match '/api/ps'
        $Verify | Should -Match 'stream = \$false'
        $Verify | Should -Match 'num_predict = 16'
        $Verify | Should -Not -Match '& ollama run'
    }

    It 'transmet Quick au benchmark depuis le menu' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
            -Action benchmark -Quick -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match '--context 8192'
        $Text | Should -Match '--qwen-thinking off'
        $Text | Should -Match '36 cas'
    }

    It 'transmet Quick à la qualification depuis le menu' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
            -Action qualification -Quick -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match 'mode QUICK'
        $Text | Should -Match 'thinking Qwen désactivé'
        $Text | Should -Match '36 cas'
    }
}
