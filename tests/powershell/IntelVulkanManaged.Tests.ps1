Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel Vulkan managed B580 hybrid runtime' {
    BeforeAll {
        $script:HybridRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:HybridRuntime = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $script:HybridBackends = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'config\v1\runtime_backends.yaml'
        )
        $script:VulkanHelper = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'scripts\windows\lib\intel_vulkan.ps1'
        )
        $script:HybridConfigure = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'scripts\windows\08_configure_openclaw.ps1'
        )
        $script:HybridE2E = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'scripts\windows\10_test_openclaw_e2e.ps1'
        )
        $script:HybridMenu = Get-Content -Raw -LiteralPath (
            Join-Path $script:HybridRepoRoot 'menu.ps1'
        )
    }

    It 'verrouille le runtime Vulkan mesuré sur un endpoint distinct de SYCL' {
        [string]$script:HybridRuntime.llama_cpp_vulkan.release | Should -Be 'b10621'
        [string]$script:HybridRuntime.llama_cpp_vulkan.asset |
            Should -Be 'llama-b10621-bin-win-vulkan-x64.zip'
        [string]$script:HybridRuntime.llama_cpp_vulkan.sha256 |
            Should -Be '2672d85bf87c8280d94dee01eb6a86280046878f70a07d786a93637fa9081163'
        [string]$script:HybridRuntime.llama_cpp_vulkan.endpoint |
            Should -Be 'http://127.0.0.1:8081/v1'
        [int]$script:HybridRuntime.llama_cpp_vulkan.listen_port | Should -Be 8081
        [int]$script:HybridRuntime.llama_cpp_vulkan.models_max | Should -Be 1
        [int]$script:HybridRuntime.llama_cpp_vulkan.parallel | Should -Be 1
        [int]$script:HybridRuntime.llama_cpp_vulkan.context_tokens | Should -Be 16384
        [string]$script:HybridRuntime.llama_cpp_vulkan.gpu_layers | Should -Be 'auto'
        @($script:HybridRuntime.llama_cpp_vulkan.managed_models) |
            Should -Be @('gemma4:26b', 'devstral-small-2:24b')
    }

    It 'gère PID intégrité B580 et mono-modèle sans réutiliser un port non suivi' {
        $script:VulkanHelper | Should -Match 'Get-FileHash'
        $script:VulkanHelper | Should -Match 'runtime-manifest\.json'
        $script:VulkanHelper | Should -Match 'server\.json'
        $script:VulkanHelper | Should -Match 'Get-NetTCPConnection'
        $script:VulkanHelper | Should -Match "'--models-max'"
        $script:VulkanHelper | Should -Match "'--models-autoload'"
        $script:VulkanHelper | Should -Match "'--gpu-layers'"
        $script:VulkanHelper | Should -Match "'--fit', 'on'"
        $script:VulkanHelper | Should -Match "'--device'"
        $script:VulkanHelper | Should -Match 'LLAMA_ARG_N_PARALLEL'
        $script:VulkanHelper | Should -Match 'Arc.*B580'
        $script:VulkanHelper | Should -Match 'Resolve-IntelSyclModelPath'
        $script:VulkanHelper | Should -Match 'AllowDownload'
        $script:VulkanHelper | Should -Match 'Invoke-IntelVulkanModelUnload'
        $script:VulkanHelper | Should -Match 'Get-IntelVulkanManagedModel'
    }

    It 'encode le profil mesuré Qwen Ollama et Gemma Devstral Vulkan sans auto-promotion' {
        $script:HybridBackends | Should -Match 'b580-hybrid:'
        $script:HybridBackends | Should -Match 'qwen-max:\s*ollama-vulkan'
        $script:HybridBackends | Should -Match 'gemma-deep:\s*llama-cpp-vulkan'
        $script:HybridBackends | Should -Match 'devstral-devops:\s*llama-cpp-vulkan'
        $script:HybridBackends | Should -Match 'recommended_candidate:\s*b580-hybrid'
        $script:HybridBackends | Should -Match 'default_backend:\s*ollama-vulkan'
        $script:HybridBackends | Should -Match 'no_automatic_promotion:\s*true'
        $script:HybridBackends | Should -Match 'rollback_backend:\s*ollama-vulkan'
    }

    It 'rend configuration et E2E conscients du provider hybride sans cloud silencieux' {
        $script:HybridConfigure | Should -Match "ValidateSet\('ollama-vulkan', 'llama-cpp-sycl', 'b580-hybrid'\)"
        $script:HybridConfigure | Should -Match 'Qwen->Ollama, Gemma/Devstral->intel-vulkan'
        $script:HybridConfigure | Should -Match 'INTEL_VULKAN_API_KEY'
        $script:HybridE2E | Should -Match "ValidateSet\('ollama-vulkan', 'llama-cpp-sycl', 'b580-hybrid'\)"
        $script:HybridE2E | Should -Match 'Get-AgentPrimaryModelRef'
        $script:HybridE2E | Should -Match 'provider_by_agent'
        $script:HybridE2E | Should -Match 'intel-vulkan/devstral-small-2:24B'
        $script:HybridE2E | Should -Match 'vulkan-tool-ok\.txt'
        $script:HybridE2E | Should -Match 'Test-ExpectedProvider'
        $script:HybridE2E | Should -Match 'Test-GatewayTransport'
    }

    It 'valide le succès applicatif, affiche un heartbeat et évite exec unattended' {
        $script:HybridE2E | Should -Match 'Test-OpenClawAgentSuccess'
        $script:HybridE2E | Should -Match 'finalAssistantVisibleText'
        $script:HybridE2E | Should -Match 'liveness invalide'
        $script:HybridE2E | Should -Match '\$SmokeText -ne \$ExpectedSmokeText'
        $script:HybridE2E | Should -Match "N'utilise aucun outil"
        $script:HybridE2E | Should -Match "'--thinking', 'off'"
        $script:HybridE2E | Should -Match "N'utilise pas exec"
        $script:HybridE2E | Should -Match 'N''utilise jamais exec'
        $script:HybridE2E | Should -Match 'Ne fais aucune vérification supplémentaire'
        $script:HybridE2E | Should -Match "\$ToolText -ne 'TOOL_OK'"
        $script:HybridE2E | Should -Match 'HeartbeatSeconds = 15'
        $script:HybridE2E | Should -Match 'Start-Job'
        $script:HybridE2E | Should -Match 'Wait-Job'
        $script:HybridE2E | Should -Match 'E2E  WAIT'
        $script:HybridE2E | Should -Match 'Remove-Job'
    }

    It 'reste compatible avec la CLI OpenClaw verrouillée 2026.7.1-2' {
        [string]$script:HybridRuntime.openclaw.preferred | Should -Be '2026.7.1-2'
        $script:HybridE2E | Should -Not -Match "'agent', 'exec'"
        $script:HybridE2E | Should -Not -Match "'--cwd'"
        $script:HybridE2E | Should -Not -Match "'--auth-env-only'"
        $script:HybridE2E | Should -Match "'--agent'"
        $script:HybridE2E | Should -Match "'--model'"
        $script:HybridE2E | Should -Match "'--session-key'"
        $script:HybridE2E | Should -Match 'Get-AgentWorkspace'
        $script:HybridE2E | Should -Match "ToolAgentId = 'ingenieur-devops'"
        $script:HybridE2E | Should -Match 'progression visible pour chaque appel long'
    }

    It 'expose setup verify stop et le profil hybride dans le menu' {
        foreach ($Action in @('intel-vulkan-setup', 'intel-vulkan-verify', 'intel-vulkan-stop')) {
            $script:HybridMenu | Should -Match ([regex]::Escape("'$Action'"))
            $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $script:HybridRepoRoot 'menu.ps1') `
                -Action $Action -DryRun 2>&1
            $LASTEXITCODE | Should -Be 0 -Because $Action
            ($Output -join "`n") | Should -Match '(?i)DRY-RUN'
        }

        $Configure = & pwsh -NoLogo -NoProfile -File (Join-Path $script:HybridRepoRoot 'menu.ps1') `
            -Action configure-openclaw -Backend b580-hybrid -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Configure -join "`n") | Should -Match 'Qwen -> Ollama; Gemma \+ Devstral -> intel-vulkan'

        $E2E = & pwsh -NoLogo -NoProfile -File (Join-Path $script:HybridRepoRoot 'menu.ps1') `
            -Action e2e -Backend b580-hybrid -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        ($E2E -join "`n") | Should -Match 'mixed-local'
    }
}
