Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Backend Intel Arc B580 SYCL' {
    It 'verrouille un binaire Windows SYCL avec SHA-256' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lock = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        [string]$Lock.llama_cpp_sycl.release | Should -Be 'b10621'
        [string]$Lock.llama_cpp_sycl.asset | Should -Be 'llama-b10621-bin-win-sycl-x64.zip'
        [string]$Lock.llama_cpp_sycl.sha256 | Should -Match '^[0-9a-f]{64}$'
        [string]$Lock.llama_cpp_sycl.oneapi_device_selector | Should -Be 'level_zero:gpu'
        [string]$Lock.llama_cpp_sycl.device | Should -Be 'SYCL0'
        [int]$Lock.llama_cpp_sycl.models_max | Should -Be 1
        [bool]$Lock.llama_cpp_sycl.offline | Should -BeTrue
    }

    It 'est fail-closed sur B580, SYCL0, Level Zero et intégrité' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl.ps1'
        )
        $Helper | Should -Match 'Get-FileHash'
        $Helper | Should -Match 'archive_sha256'
        $Helper | Should -Match 'server_sha256'
        $Helper | Should -Match 'runtime-manifest\.json'
        $Helper | Should -Match 'ONEAPI_DEVICE_SELECTOR'
        $Helper | Should -Match 'oneapi_device_selector'
        $Helper | Should -Match '--list-devices'
        $Helper | Should -Match 'Arc.*B580'
        $Helper | Should -Match 'DriverVersion'
        $Helper | Should -Match 'Get-NetTCPConnection'
        $Helper | Should -Match 'processus non suivi'
        $Helper | Should -Match "'--models-max'"
        $Helper | Should -Match "'--models-autoload'"
        $Helper | Should -Match "'--offline'"
        $Helper | Should -Match "'--device'"
        $Helper | Should -Match 'Resolve-OllamaGgufPath'
    }

    It 'génère un preset routeur versionné et mono-modèle' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl.ps1'
        )
        $Helper | Should -Match "'version = 1'"
        $Helper | Should -Match "'load-on-startup = false'"
        $Helper | Should -Match "'stop-timeout = 30'"
    }

    It 'garde Ollama comme rollback et interdit la promotion automatique' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Backends = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_backends.yaml'
        )
        $Backends | Should -Match 'default_backend:\s*ollama-vulkan'
        $Backends | Should -Match 'no_automatic_promotion:\s*true'
        $Backends | Should -Match 'rollback_backend:\s*ollama-vulkan'
        $Backends | Should -Match 'provider_id:\s*intel-sycl'
        $Backends | Should -Match 'device_api:\s*level_zero'
    }

    It 'expose tous les parcours Intel en DryRun sans matériel externe' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        foreach ($Action in @(
            'intel-sycl-setup',
            'intel-sycl-verify',
            'intel-sycl-compare',
            'intel-sycl-stop'
        )) {
            $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
                -Action $Action -DryRun 2>&1
            $LASTEXITCODE | Should -Be 0 -Because $Action
            ($Output -join "`n") | Should -Match '(?i)DRY-RUN'
        }
    }

    It 'expose la bascule OpenClaw SYCL avec rollback explicite' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $TestRepoRoot 'menu.ps1') `
            -Action configure-openclaw -Backend llama-cpp-sycl -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match 'llama-cpp-sycl'
        $Text | Should -Match 'texte -> intel-sycl'
        $Text | Should -Match 'image/PDF -> Ollama'
        $Text | Should -Match 'Rollback explicite'
    }

    It 'rend le E2E backend-aware sans accepter un fallback de provider' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $E2E = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\10_test_openclaw_e2e.ps1'
        )
        $E2E | Should -Match "ValidateSet\('ollama-vulkan', 'llama-cpp-sycl'\)"
        $E2E | Should -Match "'intel-sycl'"
        $E2E | Should -Match 'Test-ExpectedProvider'
        $E2E | Should -Match 'tool-call-ok\.txt'
        $E2E | Should -Match 'repair-ok\.txt'
    }

    It 'compare les backends sans jamais autoriser une promotion automatique' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Runner = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\28_compare_local_backends.py'
        )
        $Runner | Should -Match 'promotion_allowed.*False'
        $Runner | Should -Match 'PROMOTION_ALLOWED=false'
        $Runner | Should -Match 'ollama-vulkan'
        $Runner | Should -Match 'llama-cpp-sycl'
    }
}
