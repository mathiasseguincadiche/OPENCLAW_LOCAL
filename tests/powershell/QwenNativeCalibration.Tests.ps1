Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Calibration Qwen native non promotionnelle' {
    It 'utilise le runtime Python géré et reste indépendante du gate HARD-40M' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Wrapper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\22_calibrate_qwen_native.ps1'
        )
        $Runner = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\50_calibrate_qwen_native.py'
        )

        $Wrapper | Should -Match 'python_runtime\.ps1'
        $Wrapper | Should -Match 'Enable-ClawLocalManagedPython'
        $Wrapper | Should -Match '& \$ManagedPython'
        $Wrapper | Should -Not -Match '&\s+python(?:\.exe)?\b'
        $Runner | Should -Match 'qualification_effect'
        $Runner | Should -Match 'promotion_allowed'
        $Runner | Should -Match 'False'
        $Runner | Should -Match 'MEASURED_WITH_LIMITS'
        $Runner | Should -Match '/api/ps'
    }

    It 'supporte un DryRun sans runtime ni modèle chargé' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $WrapperPath = Join-Path $TestRepoRoot 'scripts\windows\22_calibrate_qwen_native.ps1'
        $Output = & pwsh -NoLogo -NoProfile -File $WrapperPath -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match 'Calibration Qwen native non promotionnelle'
        $Text | Should -Match 'max_out=1536'
        $Text | Should -Match 'timeout=480s'
        $Text | Should -Match 'Aucune qualification'
    }
}
