Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL model sources' {
    It 'réutilise les blobs GGUF Ollama pour la flotte B580 actuelle' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lock = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $Catalog = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\model_catalog.yaml'
        )

        [string]$Lock.llama_cpp_sycl.model_source_policy |
            Should -Be 'ollama_blob_unless_native_override'
        @($Lock.llama_cpp_sycl.native_model_overrides.PSObject.Properties).Count |
            Should -Be 0

        $Catalog | Should -Match 'provider:\s*ollama'
        $Catalog | Should -Match 'runtime_id:\s*qwen3\.5:9b-q4_K_M'
        $Catalog | Should -Match 'runtime_id:\s*gemma3:12b-it-q4_K_M'
        $Catalog | Should -Match 'runtime_id:\s*qwen2\.5-coder:14b-instruct-q4_K_M'
    }

    It 'conserve le téléchargement natif reprenable et fail-closed si un override futur est ajouté' {
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
        $Setup | Should -Match 'Les trois modèles utilisent le blob GGUF Ollama'
        $Setup | Should -Match "Aucun override natif n''est requis"
        $Helper | Should -Match 'function New-IntelSyclModelPreset'
        $Helper | Should -Match '-AllowDownload'
    }
}
