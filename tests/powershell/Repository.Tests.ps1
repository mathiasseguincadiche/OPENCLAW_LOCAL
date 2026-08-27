Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

    function Get-WindowsScript {
        Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'scripts\windows') -Filter '*.ps1'
    }
}

Describe 'Contrats PowerShell 7' {
    It 's''exécute sous PowerShell 7 ou supérieur' {
        $PSVersionTable.PSVersion.Major | Should -BeGreaterOrEqual 7
    }

    It 'parse tous les scripts PowerShell sans erreur' {
        $AllScripts = @(
            Get-Item -LiteralPath (Join-Path $RepoRoot 'menu.ps1')
            Get-WindowsScript
        )

        foreach ($Script in $AllScripts) {
            $Tokens = $null
            $ParseErrors = $null
            [void][System.Management.Automation.Language.Parser]::ParseFile(
                $Script.FullName,
                [ref]$Tokens,
                [ref]$ParseErrors
            )
            @($ParseErrors).Count | Should -Be 0 -Because $Script.FullName
        }
    }

    It 'expose DryRun sur chaque script opérationnel Windows' {
        foreach ($Script in (Get-WindowsScript)) {
            $Tokens = $null
            $ParseErrors = $null
            $Ast = [System.Management.Automation.Language.Parser]::ParseFile(
                $Script.FullName,
                [ref]$Tokens,
                [ref]$ParseErrors
            )
            @($ParseErrors).Count | Should -Be 0
            $ParameterNames = @(
                $Ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath }
            )
            $ParameterNames | Should -Contain 'DryRun' -Because $Script.Name
        }
    }

    It 'contient les scripts de phase 3 attendus' {
        $Expected = @(
            '00_bootstrap.ps1',
            '08_configure_openclaw.ps1',
            '09_deploy_agents.ps1',
            '10_test_openclaw_e2e.ps1',
            '11_install_full.ps1'
        )
        $Actual = @(Get-WindowsScript | Select-Object -ExpandProperty Name)
        foreach ($Name in $Expected) {
            $Actual | Should -Contain $Name
        }
    }

    It 'expose les actions runtime et E2E via le menu' {
        $Menu = Get-Content -LiteralPath (Join-Path $RepoRoot 'menu.ps1') -Raw
        foreach ($Action in @('install-core', 'install-full', 'configure-openclaw', 'deploy-agents', 'e2e')) {
            $Menu | Should -Match ([regex]::Escape("'$Action'"))
        }
    }

    It 'versionne les runtimes Windows supportés' {
        $LockPath = Join-Path $RepoRoot 'config\v1\runtime_versions.json'
        Test-Path -LiteralPath $LockPath | Should -BeTrue
        $Lock = Get-Content -Raw -LiteralPath $LockPath | ConvertFrom-Json
        [int]$Lock.powershell.minimum_major | Should -BeGreaterOrEqual 7
        @($Lock.python.supported) | Should -Contain '3.12'
        @($Lock.python.supported) | Should -Contain '3.13'
        [string]$Lock.openclaw.preferred | Should -Not -BeNullOrEmpty
        [string]$Lock.openclaw.integrity | Should -Match '^sha512-'
        [string]$Lock.node.sha256_win_x64_zip | Should -Match '^[0-9a-f]{64}$'
    }

    It 'conserve une politique outils fail-closed' {
        $Policy = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot 'config\v1\tool_policy.yaml')
        $Policy | Should -Match 'fs_workspace_only:\s*true'
        $Policy | Should -Match 'exec_mode:\s*ask'
        $Policy | Should -Match 'elevated_enabled:\s*false'
        $Policy | Should -Match 'cloud_tools_without_explicit_escalation:\s*false'
    }

    It 'utilise explicitement pwsh sans profil dans START_MENU.cmd' {
        $Launcher = Get-Content -LiteralPath (Join-Path $RepoRoot 'START_MENU.cmd') -Raw
        $Launcher | Should -Match '(?i)\bpwsh\b'
        $Launcher | Should -Match '(?i)-NoProfile'
        $Launcher | Should -Match '(?i)menu\.ps1'
    }

    It 'expose la documentation via le menu sans mutation' {
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $RepoRoot 'menu.ps1') -Action docs 2>&1
        $LASTEXITCODE | Should -Be 0
        ($Output -join "`n") | Should -Match 'docs[\\/]README\.md'
    }

    It 'valide les nouveaux parcours en DryRun sans runtime externe' {
        foreach ($Action in @('configure-openclaw', 'deploy-agents', 'e2e')) {
            $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $RepoRoot 'menu.ps1') `
                -Action $Action -DryRun 2>&1
            $LASTEXITCODE | Should -Be 0 -Because $Action
            ($Output -join "`n") | Should -Match '(?i)DRY-RUN'
        }
    }

    It 'conserve un DryRun de qualification explicitement sans cloud' {
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $RepoRoot 'menu.ps1') `
            -Action qualification -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match '(?i)sans appel cloud'
        $Text | Should -Match '(?i)aucune promotion automatique'
    }
}
