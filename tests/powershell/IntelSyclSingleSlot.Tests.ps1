Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL single-slot runtime contract' {
    It 'verrouille un seul slot pour un seul gros modèle' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lock = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json

        [int]$Lock.llama_cpp_sycl.models_max | Should -Be 1
        [int]$Lock.llama_cpp_sycl.parallel | Should -Be 1
        [string]$Lock.llama_cpp_sycl.gpu_layers | Should -Be 'auto'
    }

    It 'transmet parallel=1 au processus routeur sans polluer le shell appelant' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Setup = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\12_setup_intel_sycl.ps1'
        )

        $Setup | Should -Match 'LLAMA_ARG_N_PARALLEL'
        $Setup | Should -Match '\$env:LLAMA_ARG_N_PARALLEL\s*=\s*\[string\]\$RuntimeLock\.parallel'
        $Setup | Should -Match 'Remove-Item Env:LLAMA_ARG_N_PARALLEL'
        $Setup | Should -Match 'single_slot_runtime_contract\s*=\s*\$true'
        $Setup | Should -Match "schema_version\s*=\s*'1\.6\.0'"
    }

    It 'documente le slot unique dans le DryRun opérateur' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Output = & pwsh -NoLogo -NoProfile -File (
            Join-Path $TestRepoRoot 'menu.ps1'
        ) -Action intel-sycl-setup -DryRun 2>&1

        $LASTEXITCODE | Should -Be 0
        ($Output -join "`n") | Should -Match '(?i)Parallel\s*:\s*1 slot'
    }
}
