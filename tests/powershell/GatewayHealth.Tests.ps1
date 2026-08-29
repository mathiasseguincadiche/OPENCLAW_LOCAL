Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    . (Join-Path $RepoRoot 'scripts\windows\lib\gateway_health.ps1')
}

Describe 'Gateway readiness Windows' {
    It 'classe le symptôme observé runtime running + port free' {
        $Probe = [pscustomobject]@{
            exit_code = 1
            text = 'gateway not ready'
            json = [pscustomobject]@{
                service = [pscustomobject]@{
                    runtime = [pscustomobject]@{ status = 'running' }
                }
                port = [pscustomobject]@{
                    port = 18789
                    status = 'free'
                }
                rpc = [pscustomobject]@{
                    ok = $false
                    error = 'gateway closed (1006 abnormal closure)'
                }
                health = [pscustomobject]@{ healthy = $false }
            }
        }

        $Snapshot = ConvertTo-OpenClawGatewayProbeSnapshot -Probe $Probe
        $Snapshot.ready | Should -BeFalse
        $Snapshot.runtime_status | Should -Be 'running'
        $Snapshot.port_status | Should -Be 'free'
        $Snapshot.rpc_ok | Should -BeFalse
        (Get-OpenClawGatewayFailureClass -Snapshot $Snapshot) |
            Should -Be 'RUNTIME_DETECTED_NO_LISTENER'
    }

    It 'attend la readiness RPC au lieu de conclure sur la première sonde' {
        $script:GatewayProbeCount = 0
        Mock Start-Sleep { }
        Mock Invoke-OpenClawCommandCapture {
            $script:GatewayProbeCount++
            $Ready = $script:GatewayProbeCount -ge 3
            return [pscustomobject]@{
                exit_code = if ($Ready) { 0 } else { 1 }
                text = if ($Ready) { '{"rpc":{"ok":true}}' } else { 'not ready' }
                json = [pscustomobject]@{
                    service = [pscustomobject]@{
                        runtime = [pscustomobject]@{ status = 'running' }
                    }
                    port = [pscustomobject]@{
                        port = 18789
                        status = if ($Ready) { 'busy' } else { 'free' }
                    }
                    rpc = [pscustomobject]@{
                        ok = $Ready
                        error = if ($Ready) { $null } else { 'not ready' }
                    }
                    health = [pscustomobject]@{ healthy = $Ready }
                }
            }
        }

        $Result = Wait-OpenClawGatewayReady -OpenClaw 'openclaw.cmd' `
            -TimeoutSeconds 5 -PollIntervalMilliseconds 1

        $Result.ready | Should -BeTrue
        $Result.attempts | Should -Be 3
        $Result.failure_class | Should -Be 'READY'
        Should -Invoke Invoke-OpenClawCommandCapture -Times 3 -Exactly
    }

    It 'redige les valeurs sensibles dans les extraits de diagnostic' {
        $SensitiveText = 'Authorization: Bearer secret-value token=abc123 OPENROUTER_API_KEY=xyz'
        $ProtectedText = Protect-OpenClawDiagnosticText -Text $SensitiveText
        $ProtectedText | Should -Not -Match 'secret-value'
        $ProtectedText | Should -Not -Match 'abc123'
        $ProtectedText | Should -Not -Match '=xyz'
        $ProtectedText | Should -Match '<redacted>'
    }

    It 'branche install-full sur la readiness et le diagnostic bornés' {
        $Installer = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'scripts\windows\11_install_full.ps1'
        )
        $Installer | Should -Match 'Wait-OpenClawGatewayReady'
        $Installer | Should -Match 'Write-OpenClawGatewayDiagnostic'
        $Installer | Should -Match 'GatewayReadyTimeoutSeconds'
        $Installer | Should -Match 'GATEWAY_FAILURE_CLASS='
        $Installer | Should -Match 'GATEWAY_DIAGNOSTIC='
    }

    It 'réutilise la même readiness avant le scénario E2E' {
        $E2E = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'scripts\windows\10_test_openclaw_e2e.ps1'
        )
        $E2E | Should -Match 'Wait-OpenClawGatewayReady'
        $E2E | Should -Match 'Write-OpenClawGatewayDiagnostic'
        $E2E | Should -Match 'GatewayReadyTimeoutSeconds'
    }
}
