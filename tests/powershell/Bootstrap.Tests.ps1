Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Contrat interne du bootstrap Windows' {
    It 'définit les helpers bootstrap et OpenClaw attendus' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $BootstrapPath = Join-Path $RepoRoot 'scripts\windows\00_bootstrap.ps1'
        $OpenClawHelperPath = Join-Path $RepoRoot 'scripts\windows\lib\bootstrap_openclaw.ps1'

        foreach ($Path in @($BootstrapPath, $OpenClawHelperPath)) {
            Test-Path -LiteralPath $Path | Should -BeTrue
            $Tokens = $null
            $ParseErrors = $null
            [void][System.Management.Automation.Language.Parser]::ParseFile(
                $Path,
                [ref]$Tokens,
                [ref]$ParseErrors
            )
            @($ParseErrors).Count | Should -Be 0 -Because $Path
        }

        $HelperAst = [System.Management.Automation.Language.Parser]::ParseFile(
            $OpenClawHelperPath,
            [ref]$null,
            [ref]$null
        )
        $HelperFunctionNames = @(
            $HelperAst.FindAll(
                { param($Node) $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] },
                $true
            ) | ForEach-Object Name
        )
        $HelperFunctionNames | Should -Contain 'Test-OpenClawPreferred'
        $HelperFunctionNames | Should -Contain 'Install-OpenClawPreferred'

        $Bootstrap = Get-Content -Raw -LiteralPath $BootstrapPath
        $Bootstrap | Should -Match [regex]::Escape("lib\bootstrap_openclaw.ps1")
        $Bootstrap | Should -Match "'Test-OpenClawPreferred'"
        $Bootstrap | Should -Match "'Install-OpenClawPreferred'"
    }

    It 'charge les helpers OpenClaw et valide le contrat avant toute installation' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $BootstrapPath = Join-Path $RepoRoot 'scripts\windows\00_bootstrap.ps1'
        $Content = (Get-Content -Raw -LiteralPath $BootstrapPath) -replace "`r`n", "`n"

        $HelperLoad = $Content.IndexOf('. $OpenClawHelperPath')
        $ContractCall = $Content.IndexOf("Test-BootstrapFunctionContract`n`nif (-not `$IsWindows)")
        $DryRunBlock = $Content.IndexOf('if ($DryRun)')
        $FirstInstall = $Content.LastIndexOf("Install-PythonPreferred`nInstall-NodePreferred")

        $HelperLoad | Should -BeGreaterOrEqual 0
        $ContractCall | Should -BeGreaterThan $HelperLoad
        $DryRunBlock | Should -BeGreaterThan $ContractCall
        $FirstInstall | Should -BeGreaterThan $DryRunBlock
    }
}
