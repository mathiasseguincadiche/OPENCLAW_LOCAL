Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Intel SYCL compare watchdog' {
    BeforeAll {
        $script:WatchdogRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:WatchdogScriptPath = Join-Path $script:WatchdogRepoRoot `
            'scripts\windows\15_compare_intel_backends.ps1'
        $script:WatchdogScript = Get-Content -Raw -LiteralPath $script:WatchdogScriptPath
    }

    It 'supervise le Python gere au lieu de bloquer le shell indefiniment' {
        $script:WatchdogScript | Should -Match 'Start-Process -FilePath \$ManagedPython'
        $script:WatchdogScript | Should -Match "@\('-u', \$CompareScript\)"
        $script:WatchdogScript | Should -Match 'Python benchmark effectif'
        $script:WatchdogScript | Should -Match 'WaitForExit\(10000\)'
        $script:WatchdogScript | Should -Match 'Watchdog: benchmark interrompu'
    }

    It 'arrete le routeur suivi et remonte ses logs si le plafond est depasse' {
        $script:WatchdogScript | Should -Match 'Stop-IntelSyclServer'
        $script:WatchdogScript | Should -Match 'Paths\.ProcessState'
        $script:WatchdogScript | Should -Match 'Paths\.StderrLog'
        $script:WatchdogScript | Should -Match 'compare_.*stdout\.log'
        $script:WatchdogScript | Should -Match 'compare_.*stderr\.log'
    }

    It 'persiste une preuve JSON fail-closed pour timeout ou sortie Python en erreur' {
        $script:WatchdogScript | Should -Match 'Write-CompareWatchdogProof'
        $script:WatchdogScript | Should -Match 'compare_watchdog_\$\{Status\}_\$\{Stamp\}\.json'
        $script:WatchdogScript | Should -Match 'INTEL_SYCL_COMPARE_WATCHDOG_PROOF='
        $script:WatchdogScript | Should -Match "promotion_allowed = \$false"
        $script:WatchdogScript | Should -Match "-Status 'timeout'"
        $script:WatchdogScript | Should -Match "-Status 'failed'"
    }

    It 'borne quick a 420 secondes et le benchmark complet a 1800 secondes' {
        $Quick = & pwsh -NoLogo -NoProfile -File $script:WatchdogScriptPath `
            -DryRun -Quick 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Quick -join "`n") | Should -Match 'Watchdog dur global=420 s'

        $Full = & pwsh -NoLogo -NoProfile -File $script:WatchdogScriptPath `
            -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Full -join "`n") | Should -Match 'Watchdog dur global=1800 s'
    }

    It 'accepte un plafond manuel raisonnable et refuse une valeur dangereusement basse' {
        $Custom = & pwsh -NoLogo -NoProfile -File $script:WatchdogScriptPath `
            -DryRun -Quick -HardTimeoutSeconds 240 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Custom -join "`n") | Should -Match 'Watchdog dur global=240 s'

        $TooLow = & pwsh -NoLogo -NoProfile -File $script:WatchdogScriptPath `
            -DryRun -Quick -HardTimeoutSeconds 60 2>&1
        $LASTEXITCODE | Should -Not -Be 0
        ($TooLow -join "`n") | Should -Match 'HardTimeoutSeconds doit valoir 0'
    }
}
