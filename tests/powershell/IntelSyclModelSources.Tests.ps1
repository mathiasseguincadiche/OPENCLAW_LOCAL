Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL model sources' {
    It 'verrouille Devstral sur un GGUF llama.cpp natif et laisse Ollama nominal intact' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lock = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $Catalog = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\model_catalog.yaml'
        )

        [string]$Lock.llama_cpp_sycl.model_source_policy |
            Should -Be 'ollama_blob_unless_native_override'
        $Override = $Lock.llama_cpp_sycl.native_model_overrides.PSObject.Properties[
            'devstral-small-2:24b'
        ].Value
        [string]$Override.architecture | Should -Be 'mistral3'
        [string]$Override.quantization | Should -Be 'Q4_K_M'
        [string]$Override.sha256 | Should -Be (
            'bfd11c8679c6b81eb43763505465d7dcfa72e460ab1c220ecc235a3efadd7f7f'
        )
        [string]$Override.url | Should -Match '^https://huggingface\.co/'
        [string]$Override.reason | Should -Match 'ollama_mistral3_layout'

        $Catalog | Should -Match 'provider:\s*ollama'
        $Catalog | Should -Match 'runtime_id:\s*devstral-small-2:24b'
    }

    It 'télécharge de façon reprenable et fail-closed sur le SHA-256' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl_model_sources.ps1'
        )

        $Helper | Should -Match 'curl\.exe'
        $Helper | Should -Match "'--continue-at'"
        $Helper | Should -Match '\.partial'
        $Helper | Should -Match 'Get-FileHash'
        $Helper | Should -Match 'SHA-256 GGUF natif'
        $Helper | Should -Match 'manifest\.json'
        $Helper | Should -Match 'Resolve-IntelSyclModelPath'
        $Helper | Should -Match 'Resolve-OllamaGgufPath'
    }

    It 'injecte la source provider-specific dans le preset du setup' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Setup = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\12_setup_intel_sycl.ps1'
        )
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl_model_sources.ps1'
        )

        $Setup | Should -Match 'intel_sycl_model_sources\.ps1'
        $Setup | Should -Match 'Devstral utilise un GGUF llama\.cpp natif'
        $Helper | Should -Match 'function New-IntelSyclModelPreset'
        $Helper | Should -Match '-AllowDownload'
        $Helper | Should -Match 'Qwen/Gemma réutilisent Ollama'
    }
}
