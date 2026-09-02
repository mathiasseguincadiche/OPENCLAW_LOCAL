Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel Vulkan isolation probe' {
    BeforeAll {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:VulkanRuntimeVersions = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $script:VulkanProbeScript = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\17_probe_intel_vulkan.ps1'
        )
        $script:VulkanMenuScript = Get-Content -Raw -LiteralPath (Join-Path $TestRepoRoot 'menu.ps1')
    }

    It 'verrouille le runtime Vulkan b10621 officiel et son SHA-256' {
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.release | Should -Be 'b10621'
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.asset |
            Should -Be 'llama-b10621-bin-win-vulkan-x64.zip'
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.sha256 |
            Should -Be '2672d85bf87c8280d94dee01eb6a86280046878f70a07d786a93637fa9081163'
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.promotion_allowed | Should -BeFalse
    }

    It 'utilise le meme contrat de charge que SYCL pour isoler le backend' {
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.context_tokens | Should -Be 16384
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.gpu_layers | Should -Be 'auto'
        $script:VulkanRuntimeVersions.llama_cpp_vulkan_probe.parallel | Should -Be 1
        $script:VulkanProbeScript | Should -Match "'--ctx-size'"
        $script:VulkanProbeScript | Should -Match "'--gpu-layers'"
        $script:VulkanProbeScript | Should -Match "'--parallel'"
        $script:VulkanProbeScript | Should -Match "'--fit', 'on'"
        $script:VulkanProbeScript | Should -Match "'--device'"
        $script:VulkanProbeScript | Should -Match 'enable_thinking = \$false'
        $script:VulkanProbeScript | Should -Match 'Resolve-IntelSyclModelPath'
    }

    It 'refuse les baselines anciennes ou structurellement incompletes' {
        $script:VulkanProbeScript | Should -Match "SchemaProperty\.Value -ne '1\.5\.0'"
        $script:VulkanProbeScript | Should -Match 'gpu_memory_isolation_between_backends'
        $script:VulkanProbeScript | Should -Match "PSObject\.Properties\['summary'\]"
        $script:VulkanProbeScript | Should -Match "PSObject\.Properties\['models'\]"
        $script:VulkanProbeScript | Should -Match "baseline_required_schema = '1\.5\.0'"
        $script:VulkanProbeScript | Should -Match 'Baseline acceptée uniquement si schéma 1\.5\.0'
    }

    It 'preserve null quand llama.cpp ne fournit pas les timings' {
        $script:VulkanProbeScript | Should -Match '\$null -ne \$Result\.tokens_per_second'
        $script:VulkanProbeScript | Should -Match 'llama_cpp_vulkan_tps = \$VulkanTps'
        $script:VulkanProbeScript | Should -Match '\$null -ne \$VulkanTps'
    }

    It 'compare la mesure Vulkan au dernier benchmark Ollama et SYCL sans promotion' {
        $script:VulkanProbeScript | Should -Match 'backend_compare_b580_\*\.json'
        $script:VulkanProbeScript | Should -Match "PSObject\.Properties\['ollama-vulkan'\]"
        $script:VulkanProbeScript | Should -Match "PSObject\.Properties\['llama-cpp-sycl'\]"
        $script:VulkanProbeScript | Should -Match 'PROMOTION_ALLOWED=false'
        $script:VulkanProbeScript | Should -Match 'openclaw_modified = \$false'
    }

    It 'expose une action menu dediee et un dry-run sans mutation' {
        $script:VulkanMenuScript | Should -Match "'intel-vulkan-probe'"
        $script:VulkanMenuScript | Should -Match '17_probe_intel_vulkan\.ps1'
        $script:VulkanProbeScript | Should -Match '\[DRY-RUN\] Probe d.+isolation llama\.cpp Vulkan'
        $script:VulkanProbeScript | Should -Match 'Aucune modification OpenClaw et aucune promotion backend'
    }
}
