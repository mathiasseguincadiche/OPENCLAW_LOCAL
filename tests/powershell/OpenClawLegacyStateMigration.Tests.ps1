Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Migration état OpenClaw 2026.7.x vers 2026.8.x' {
    BeforeAll {
        $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:MigrationScript = Join-Path $script:RepoRoot `
            'scripts\windows\lib\openclaw_legacy_state.ps1'
        $script:ConfigureSource = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
        )
    }

    It 'retire uniquement les clés retirées et préserve la valeur PDF' {
        $ConfigPath = Join-Path $TestDrive 'openclaw.json'
        [ordered]@{
            meta = [ordered]@{
                lastTouchedAt = '2026-09-03T00:00:00Z'
                lastTouchedVersion = '2026.7.1-2'
            }
            agents = [ordered]@{
                defaults = [ordered]@{
                    pdfMaxBytesMb = 48
                    compaction = [ordered]@{
                        mode = 'safeguard'
                        reserveTokens = 4096
                        reserveTokensFloor = 4096
                    }
                }
            }
        } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $ConfigPath -Encoding utf8

        & $script:MigrationScript -ConfigPath $ConfigPath

        $Migrated = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
        $Migrated.meta.PSObject.Properties['lastTouchedAt'] | Should -BeNullOrEmpty
        [string]$Migrated.meta.lastTouchedVersion | Should -Be '2026.7.1-2'
        $Migrated.agents.defaults.PSObject.Properties['pdfMaxBytesMb'] | Should -BeNullOrEmpty
        [int]$Migrated.agents.defaults.pdfMaxMb | Should -Be 48
        $Migrated.agents.defaults.compaction.PSObject.Properties['reserveTokens'] |
            Should -BeNullOrEmpty
        $Migrated.agents.defaults.compaction.PSObject.Properties['reserveTokensFloor'] |
            Should -BeNullOrEmpty
        [string]$Migrated.agents.defaults.compaction.mode | Should -Be 'safeguard'
        @(Get-ChildItem -LiteralPath $TestDrive -Filter 'openclaw.json.pre-2026.8.2-*.bak').Count |
            Should -Be 1
    }

    It 'ne remplace pas une valeur pdfMaxMb déjà canonique' {
        $ConfigPath = Join-Path $TestDrive 'openclaw-existing-canonical.json'
        [ordered]@{
            agents = [ordered]@{
                defaults = [ordered]@{
                    pdfMaxBytesMb = 48
                    pdfMaxMb = 64
                }
            }
        } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $ConfigPath -Encoding utf8

        & $script:MigrationScript -ConfigPath $ConfigPath

        $Migrated = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
        [int]$Migrated.agents.defaults.pdfMaxMb | Should -Be 64
        $Migrated.agents.defaults.PSObject.Properties['pdfMaxBytesMb'] | Should -BeNullOrEmpty
    }

    It 'exécute la pré-migration avant le premier inventaire plugin OpenClaw' {
        $MigrationIndex = $script:ConfigureSource.IndexOf(
            'Invoke-OpenClawLegacyStateMigration -ConfigPath $ConfigPath'
        )
        $PluginIndex = $script:ConfigureSource.IndexOf(
            'Initialize-ParallelSearchPlugin -OpenClaw $OpenClaw'
        )
        $MigrationIndex | Should -BeGreaterThan -1
        $PluginIndex | Should -BeGreaterThan -1
        $MigrationIndex | Should -BeLessThan $PluginIndex
    }
}
