Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL process output contract' {
    It 'ne laisse pas WaitForExit contaminer le success pipeline' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        . (Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl_process_contract.ps1')

        Mock Test-Path { $true }
        Mock Get-Content { '{"pid":4242}' }
        Mock Get-Process {
            $Process = [pscustomobject]@{ Id = 4242 }
            $Process | Add-Member -MemberType ScriptMethod -Name WaitForExit -Value {
                param($Timeout)
                if ($Timeout -lt 0) {
                    throw 'Timeout invalide.'
                }
                return $true
            }
            return $Process
        }
        Mock Stop-Process { }
        Mock Remove-Item { }

        $Output = @(Stop-IntelSyclServer -StatePath 'X:\state\server.json' -Confirm:$false)
        $Output.Count | Should -Be 0
    }

    It 'charge le contrat strict avant le setup et le stop opérationnels' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        foreach ($ScriptName in @('12_setup_intel_sycl.ps1', '13_stop_intel_sycl.ps1')) {
            $Script = Get-Content -Raw -LiteralPath (
                Join-Path $TestRepoRoot "scripts\windows\$ScriptName"
            )
            $Script | Should -Match 'intel_sycl_process_contract\.ps1'
        }

        $Setup = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\12_setup_intel_sycl.ps1'
        )
        $Setup | Should -Match 'strict_process_output_contract\s*=\s*\$true'
        $Setup | Should -Match "PSObject\.Properties\['Process'\]"
    }
}
