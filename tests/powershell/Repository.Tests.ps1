Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $WindowsScripts = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'scripts\windows') -Filter '*.ps1'
}

Describe 'Contrats PowerShell 7' {
    It 's''exécute sous PowerShell 7 ou supérieur' {
        $PSVersionTable.PSVersion.Major | Should -BeGreaterOrEqual 7
    }

    It 'parse tous les scripts PowerShell sans erreur' {
        $AllScripts = @(
            Get-Item -LiteralPath (Join-Path $RepoRoot 'menu.ps1')
            $WindowsScripts
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
        foreach ($Script in $WindowsScripts) {
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

    It 'conserve un DryRun de qualification explicitement sans cloud' {
        $Output = & pwsh -NoLogo -NoProfile -File (Join-Path $RepoRoot 'menu.ps1') `
            -Action qualification -DryRun 2>&1
        $LASTEXITCODE | Should -Be 0
        $Text = $Output -join "`n"
        $Text | Should -Match '(?i)sans appel cloud'
        $Text | Should -Match '(?i)aucune promotion automatique'
    }
}
