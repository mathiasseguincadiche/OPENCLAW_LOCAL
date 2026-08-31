Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL direct model diagnostic' {
    It 'expose la matrice fit on, fit off et CPU-only' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\16_diagnose_intel_sycl_model.ps1'
        )

        $Script | Should -Match "'gpu_fit_on'"
        $Script | Should -Match "'gpu_fit_off'"
        $Script | Should -Match "'cpu_fit_off'"
        $Script | Should -Match "-Fit 'on'"
        $Script | Should -Match "-Fit 'off'"
        $Script | Should -Match "-GpuLayers 'all'"
        $Script | Should -Match "-GpuLayers '0'"
        $Script | Should -Match 'Resolve-OllamaGgufPath'
        $Script | Should -Match 'RedirectStandardError'
        $Script | Should -Match 'RedirectStandardOutput'
    }

    It 'classe les causes sans modifier OpenClaw' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\16_diagnose_intel_sycl_model.ps1'
        )

        $Script | Should -Match 'router_only_or_transient'
        $Script | Should -Match 'llama_fit_regression'
        $Script | Should -Match 'sycl_offload_or_device_memory'
        $Script | Should -Match 'gguf_or_llama_core_load'
        $Script | Should -Match 'openclaw_modified = \$false'
        $Script | Should -Match 'INTEL_SYCL_MODEL_DIAGNOSTIC='
        $Script | Should -Match 'DIAGNOSIS='
    }

    It 'est accessible depuis le menu et passe en DryRun' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Menu = Get-Content -Raw -LiteralPath (Join-Path $TestRepoRoot 'menu.ps1')
        $Menu | Should -Match "'intel-sycl-diagnose'"
        $Menu | Should -Match '16_diagnose_intel_sycl_model\.ps1'
        $Menu | Should -Match 'ModelMode'

        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
            -Action intel-sycl-diagnose -Model devstral-small-2:24b -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Output -join "`n") | Should -Match '(?i)DRY-RUN'
        ($Output -join "`n") | Should -Match 'gpu_fit_on'
        ($Output -join "`n") | Should -Match 'cpu_fit_off'
    }
}
