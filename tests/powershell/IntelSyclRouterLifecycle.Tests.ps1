Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL router model lifecycle' {
    It 'utilise l endpoint officiel models unload et attend la libération' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Lifecycle = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl_model_lifecycle.ps1'
        )
        $Lifecycle | Should -Match '/models/unload'
        $Lifecycle | Should -Match 'Wait-IntelSyclModelUnloaded'
        $Lifecycle | Should -Match 'Get-IntelSyclRouterModelInventory'
        $Lifecycle | Should -Match "Status -eq 'unloaded'"
        $Lifecycle | Should -Match 'models\?reload=1'
        $Lifecycle | Should -Match "-replace '/v1\$', ''"
        $Lifecycle | Should -Match 'Remove-IntelSyclModel'
        $Lifecycle | Should -Match 'SupportsShouldProcess'
    }

    It 'décharge chaque modèle entre les smokes setup et verify' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        foreach ($ScriptName in @(
            '12_setup_intel_sycl.ps1',
            '14_verify_intel_sycl.ps1'
        )) {
            $Script = Get-Content -Raw -LiteralPath (
                Join-Path $TestRepoRoot "scripts\windows\$ScriptName"
            )
            $Script | Should -Match 'intel_sycl_model_lifecycle\.ps1'
            $Script | Should -Match 'Remove-IntelSyclModel'
            $Script | Should -Match '-Confirm:\$false'
            $Script | Should -Match 'unloaded_after_smoke'
            $Script | Should -Match 'DiagnosticLogPath'
        }
    }

    It 'remonte le stderr du child server lors d un échec HTTP' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Smoke = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl_smoke.ps1'
        )
        $Smoke | Should -Match 'DiagnosticLogPath'
        $Smoke | Should -Match 'Get-Content.*-Tail 120'
        $Smoke | Should -Match 'Smoke Intel SYCL HTTP échoué'
        $Smoke | Should -Match 'Dernières lignes llama-server'
    }
}
