Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL process output contract' {
    It 'ne laisse pas WaitForExit contaminer le success pipeline' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        . (Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl.ps1')

        $StatePath = Join-Path $TestDrive 'server.json'
        '{"pid":4242}' | Set-Content -LiteralPath $StatePath -Encoding utf8

        Mock Get-Process {
            param($Id)
            if ($Id -ne 4242) {
                throw "PID inattendu: $Id"
            }
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
        Mock Stop-Process {
            param($Id, [switch]$Force)
            if ($Id -ne 4242 -or -not $Force) {
                throw 'Stop-Process n a pas reçu le PID et Force attendus.'
            }
        }

        $Output = @(Stop-IntelSyclServer -StatePath $StatePath -Confirm:$false)
        $Output.Count | Should -Be 0
        Test-Path -LiteralPath $StatePath | Should -BeFalse
    }

    It 'conserve une seule implémentation canonique et des call sites stricts' {
        $TestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $Helper = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\lib\intel_sycl.ps1'
        )
        $Helper | Should -Match '\$null\s*=\s*\$Process\.WaitForExit\(10000\)'
        $Helper | Should -Match '\$null\s*=\s*Stop-IntelSyclServer.*-Confirm:\$false'

        $Setup = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\12_setup_intel_sycl.ps1'
        )
        $Setup | Should -Match 'strict_process_output_contract\s*=\s*\$true'
        $Setup | Should -Match "PSObject\.Properties\['Process'\]"
        $Setup | Should -Match '\$null\s*-eq\s*\$Server\.Process'
        $Setup | Should -Not -Match 'intel_sycl_process_contract\.ps1'

        $Stop = Get-Content -Raw -LiteralPath (
            Join-Path $TestRepoRoot 'scripts\windows\13_stop_intel_sycl.ps1'
        )
        $Stop | Should -Match 'Stop-IntelSyclServer.*-Confirm:\$false'
        $Stop | Should -Not -Match 'intel_sycl_process_contract\.ps1'
    }
}
