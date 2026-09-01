$ErrorActionPreference = 'Stop'

Describe 'Intel Vulkan isolation probe' {
    BeforeAll {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $RuntimeVersions = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $ProbeScript = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\17_probe_intel_vulkan.ps1'
        )
        $MenuScript = Get-Content -Raw -LiteralPath (Join-Path $TestRepoRoot 'menu.ps1')
    }

    It 'verrouille le runtime Vulkan b10621 officiel et son SHA-256' {
        $RuntimeVersions.llama_cpp_vulkan_probe.release | Should -Be 'b10621'
        $RuntimeVersions.llama_cpp_vulkan_probe.asset |
            Should -Be 'llama-b10621-bin-win-vulkan-x64.zip'
        $RuntimeVersions.llama_cpp_vulkan_probe.sha256 |
            Should -Be '2672d85bf87c8280d94dee01eb6a86280046878f70a07d786a93637fa9081163'
        $RuntimeVersions.llama_cpp_vulkan_probe.promotion_allowed | Should -BeFalse
    }

    It 'utilise le meme contrat de charge que SYCL pour isoler le backend' {
        $RuntimeVersions.llama_cpp_vulkan_probe.context_tokens | Should -Be 8192
        $RuntimeVersions.llama_cpp_vulkan_probe.gpu_layers | Should -Be 'auto'
        $RuntimeVersions.llama_cpp_vulkan_probe.parallel | Should -Be 1
        $ProbeScript | Should -Match "'--ctx-size'"
        $ProbeScript | Should -Match "'--gpu-layers'"
        $ProbeScript | Should -Match "'--parallel'"
        $ProbeScript | Should -Match "'--fit', 'on'"
        $ProbeScript | Should -Match "'--device'"
        $ProbeScript | Should -Match 'enable_thinking = \$false'
        $ProbeScript | Should -Match 'Resolve-IntelSyclModelPath'
    }

    It 'compare la mesure Vulkan au dernier benchmark Ollama et SYCL sans promotion' {
        $ProbeScript | Should -Match 'backend_compare_b580_\*\.json'
        $ProbeScript | Should -Match "PSObject\.Properties\['ollama-vulkan'\]"
        $ProbeScript | Should -Match "PSObject\.Properties\['llama-cpp-sycl'\]"
        $ProbeScript | Should -Match 'PROMOTION_ALLOWED=false'
        $ProbeScript | Should -Match 'openclaw_modified = \$false'
    }

    It 'expose une action menu dediee et un dry-run sans mutation' {
        $MenuScript | Should -Match "'intel-vulkan-probe'"
        $MenuScript | Should -Match '17_probe_intel_vulkan\.ps1'
        $ProbeScript | Should -Match '\[DRY-RUN\] Probe d''isolation llama\.cpp Vulkan'
        $ProbeScript | Should -Match 'Aucune modification OpenClaw et aucune promotion backend'
    }
}
