Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $RuntimeLockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
    $RuntimeLock = Get-Content -Raw -LiteralPath $RuntimeLockPath | ConvertFrom-Json
    $ConfigureScript = Join-Path $RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
}

Describe 'Contrat OpenClaw 2026.9.2' {
    It 'verrouille exactement OpenClaw 2026.9.2 et son artefact npm' {
        [string]$RuntimeLock.openclaw.package | Should -Be 'openclaw'
        [string]$RuntimeLock.openclaw.preferred | Should -Be '2026.9.2'
        [string]$RuntimeLock.openclaw.release_sha | Should -Be '3928bad9badfcb6c7d140530435e806fb8092190'
        [string]$RuntimeLock.openclaw.integrity | Should -Be (
            'sha512-M6C7UsnX815nv26qBJFYGe6aGzv+ftZLRzV6S9oRXUtXg2Yn67eVntpssT94kgkquKVSeUxerUg0j1ONp4WYQg=='
        )
    }

    It 'aligne exactement le plugin Parallel sur OpenClaw 2026.9.2' {
        [string]$RuntimeLock.openclaw.plugins.parallel.package | Should -Be '@openclaw/parallel-plugin'
        [string]$RuntimeLock.openclaw.plugins.parallel.preferred | Should -Be '2026.9.2'
        [string]$RuntimeLock.openclaw.plugins.parallel.provider | Should -Be 'parallel-free'
    }

    It 'affiche 2026.9.2 comme version verrouillée dans configure-openclaw DryRun' {
        $Output = & pwsh -NoLogo -NoProfile -File $ConfigureScript -DryRun 2>&1
        $Text = $Output -join "`n"

        $LASTEXITCODE | Should -Be 0 -Because $Text
        $Text | Should -Match ([regex]::Escape('OpenClaw   : 2026.9.2 (version verrouillée)'))
        $Text | Should -Not -Match '2026\.9\.1'
    }
}
