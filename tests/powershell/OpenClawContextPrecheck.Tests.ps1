Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Régression OpenClaw context precheck local' {
    BeforeAll {
        $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script:Runtime = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'config\v1\runtime_versions.json'
        ) | ConvertFrom-Json
        $script:ModelCatalog = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'config\v1\model_catalog.yaml'
        )
        $script:Configure = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\08_configure_openclaw.ps1'
        )
        $script:Admission = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\24_test_openclaw_prompt_admission.ps1'
        )
        $script:E2E = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'scripts\windows\10_test_openclaw_e2e.ps1'
        )
        $script:Generator = Get-Content -Raw -LiteralPath (
            Join-Path $script:RepoRoot 'src\clawlocal\openclaw_config.py'
        )
    }

    It 'verrouille la stable OpenClaw 2026.9.1 et son artefact npm exact' {
        [string]$script:Runtime.openclaw.preferred | Should -Be '2026.9.1'
        [string]$script:Runtime.openclaw.integrity | Should -Be (
            'sha512-0Ve0631CdgkJDwd4NNG1BawIdF5yCL2sO+Tts8amStw+H6vKURTj0K4r' +
            'Oa4+hFpJk1Dnw5LyKl5twzwX1VtA2w=='
        )
        [string]$script:Runtime.openclaw.release_sha |
            Should -Be 'ad6fe23aecb9b833d68139b0ddc9f239b894d2f1'
        [string]$script:Runtime.openclaw.plugins.parallel.preferred | Should -Be '2026.9.1'
    }

    It 'reste fail-closed sur la version runtime avant de muter OpenClaw' {
        $script:Configure | Should -Match 'Assert-OpenClawVersion'
        $script:Configure | Should -Match 'ExpectedOpenClawVersion'
        $script:Configure | Should -Match 'install-core avant configure-openclaw'
        $VersionIndex = $script:Configure.IndexOf(
            'Assert-OpenClawVersion -OpenClaw $OpenClaw'
        )
        $PatchIndex = $script:Configure.IndexOf(
            "'config', 'patch', '--file', `$PatchPath, '--dry-run'"
        )
        $VersionIndex | Should -BeGreaterThan -1
        $PatchIndex | Should -BeGreaterThan -1
        $VersionIndex | Should -BeLessThan $PatchIndex
    }

    It 'sépare benchmark 8K et orchestration OpenClaw 16K sans anciens overrides reserve' {
        $script:ModelCatalog | Should -Match 'nominal_context_tokens: 8192'
        $script:ModelCatalog | Should -Match 'openclaw_agent_context_tokens: 16384'
        $script:ModelCatalog | Should -Match 'openclaw_agent_context_is_benchmark_promotion: false'
        $script:Generator | Should -Match 'openclaw_agent_context_tokens'
        $script:Generator | Should -Match '"contextWindow": context_tokens'
        $script:Generator | Should -Match '"contextTokens": context_tokens'
        $script:Generator | Should -Match '"num_ctx": context_tokens'
        $script:Generator | Should -Not -Match 'reserveTokensFloor'
        $script:Generator | Should -Not -Match '"reserveTokens"'
        $script:Generator | Should -Not -Match 'pdfMaxBytesMb'
        $script:Generator | Should -Match '"pdfMaxMb"'
    }

    It 'réduit le prompt statique au lieu de compter sur une hausse de contexte seule' {
        $script:Generator | Should -Match 'skipOptionalBootstrapFiles'
        $script:Generator | Should -Match 'OPTIONAL_BOOTSTRAP_FILES'
        $script:Generator | Should -Match '"toolSearch"'
        $script:Generator | Should -Match '"mode": "tools"'
        $script:Generator | Should -Match '"profile": tool_policy'
    }

    It 'refuse un configure nominal tant que les trois familles ne passent pas un vrai prompt agent' {
        $script:Configure | Should -Match '24_test_openclaw_prompt_admission\.ps1'
        $script:Configure | Should -Match "'chef-operations', 'architecte-solutions', 'ingenieur-devops'"
        $script:Configure | Should -Match 'Admission prompt validée sur Qwen 3\.5, Gemma 3 et Qwen 2\.5 Coder'
        $script:Admission | Should -Match 'PROMPT_ADMISSION_EVIDENCE='
        $script:Admission | Should -Match 'systemPromptReport'
        $script:Admission | Should -Match 'PROMPT_ADMISSION_SYSTEM_CHARS='
        $script:Admission | Should -Match 'Contrôle d admission OpenClaw refusé'
    }

    It 'lit le roster canonique 2026.9.x tout en gardant la compatibilité list' {
        $script:E2E | Should -Match "PSObject\.Properties\['entries'\]"
        $script:E2E | Should -Match "PSObject\.Properties\['list'\]"
        $script:E2E | Should -Match 'roster canonique agents\.entries'
        $script:E2E | Should -Match 'runtime_versions\.json'
    }
}
