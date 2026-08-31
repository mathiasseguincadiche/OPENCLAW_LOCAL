Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL direct model diagnostic' {
    It 'expose full offload, fit off, auto offload et CPU-only' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\16_diagnose_intel_sycl_model.ps1'
        )

        $Script | Should -Match "'gpu_fit_on'"
        $Script | Should -Match "'gpu_fit_off'"
        $Script | Should -Match "'gpu_auto_fit_on'"
        $Script | Should -Match "'cpu_fit_off'"
        $Script | Should -Match "-Fit 'on'"
        $Script | Should -Match "-Fit 'off'"
        $Script | Should -Match "-GpuLayers 'all'"
        $Script | Should -Match "-GpuLayers 'auto'"
        $Script | Should -Match "-GpuLayers '0'"
        $Script | Should -Match 'Resolve-IntelSyclModelPath'
        $Script | Should -Match 'intel_sycl_model_sources\.ps1'
        $Script | Should -Match 'RedirectStandardError'
        $Script | Should -Match 'RedirectStandardOutput'
        $Script | Should -Match 'STDERR'
    }

    It 'classe les causes sans modifier OpenClaw' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Script = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\16_diagnose_intel_sycl_model.ps1'
        )

        $Script | Should -Match 'nominal_direct_load'
        $Script | Should -Match 'llama_fit_regression'
        $Script | Should -Match 'automatic_partial_offload_required'
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
        $Text = $Output -join "`n"
        $Text | Should -Match '(?i)DRY-RUN'
        $Text | Should -Match 'SYCL/all\+fit on'
        $Text | Should -Match 'SYCL/auto\+fit on'
        $Text | Should -Match 'CPU/0\+fit off'
        $Text | Should -Match 'overrides natifs'
    }
}
