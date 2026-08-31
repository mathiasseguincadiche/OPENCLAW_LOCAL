Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL B580 auto-fit policy' {
    It 'laisse llama.cpp ajuster les couches GPU au lieu de forcer all' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lock = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        [string]$Lock.llama_cpp_sycl.gpu_layers | Should -Be 'auto'

        $Backends = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'config\v1\runtime_backends.yaml'
        )
        $Backends | Should -Match 'gpu_layers:\s*auto'
        $Backends | Should -Not -Match 'gpu_layers:\s*all'

        $HardwareProfile = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'config\v1\hardware_profiles\intel_arc_b580_12gb.yaml'
        )
        $HardwareProfile | Should -Match 'sycl_gpu_layers:\s*auto'
    }

    It 'transmet la politique runtime au serveur sans override caché' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'scripts\windows\lib\intel_sycl.ps1'
        )
        $Helper | Should -Match "'--gpu-layers'"
        $Helper | Should -Match 'RuntimeLock\.gpu_layers'
    }
}
