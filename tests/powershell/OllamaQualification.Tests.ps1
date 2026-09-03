Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Qualification Ollama lisible et bornée' {
    It 'utilise l API chat locale pour le smoke test et non ollama run' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Verify = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\04_verify_local.ps1'
        )
        $Verify | Should -Match '/api/chat'
        $Verify | Should -Match '/api/ps'
        $Verify | Should -Match 'stream = \$false'
        $Verify | Should -Match 'num_predict = 64'
        $Verify | Should -Match "gemma4:\*"
        $Verify | Should -Match '\$RequestBody\.think = \$false'
        $Verify | Should -Match 'thinking_chars='
        $Verify | Should -Match 'done_reason='
        $Verify | Should -Not -Match '/api/generate'
        $Verify | Should -Not -Match '& ollama run'
    }

    It 'exécute benchmark et évaluation avec le Python géré OPENCLAW_LOCAL' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        foreach ($RelativePath in @(
            'scripts\windows\05_benchmark.ps1',
            'scripts\windows\07_run_qualification.ps1'
        )) {
            $Script = Get-Content -Raw -LiteralPath (Join-Path $TestRepoRoot $RelativePath)
            $Script | Should -Match 'python_runtime\.ps1'
            $Script | Should -Match 'Enable-ClawLocalManagedPython'
            $Script | Should -Match '& \$ManagedPython'
            $Script | Should -Not -Match '&\s+python(?:\.exe)?\b'
        }
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
        $Text | Should -Match 'Python géré OPENCLAW_LOCAL'
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
        $Text | Should -Match 'environnement géré OPENCLAW_LOCAL'
    }
}

Describe 'Inventaire VRAM Windows fiable' {
    It 'préfère QWORD et ne traite pas le fallback 32 bits comme fiable' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $InventoryHelper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\hardware_inventory.ps1'
        )
        $InventoryHelper | Should -Match 'HardwareInformation\.qwMemorySize'
        $InventoryHelper | Should -Match 'windows_registry_hardware_information_qword'
        $InventoryHelper | Should -Match 'HardwareInformation\.MemorySize'
        $InventoryHelper | Should -Match 'windows_registry_hardware_information_legacy32'
        $InventoryHelper | Should -Match 'reliable = \$IsQword'
    }
}
