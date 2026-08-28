Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Describe 'Contrat interne du bootstrap Windows' {
    It 'définit tous les helpers critiques avant installation' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $BootstrapPath = Join-Path $RepoRoot 'scripts\windows\00_bootstrap.ps1'
        $Tokens = $null
        $ParseErrors = $null
        $Ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $BootstrapPath,
            [ref]$Tokens,
            [ref]$ParseErrors
        )
        @($ParseErrors).Count | Should -Be 0

        $FunctionNames = @(
            $Ast.FindAll(
                { param($Node) $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] },
                $true
            ) | ForEach-Object Name
        )

        $Required = @(
            'Write-BootstrapFailure',
            'Get-PlatformRoot',
            'Invoke-NativeChecked',
            'Test-PythonPreferred',
            'Invoke-PreferredPython',
            'Install-PythonPreferred',
            'Test-NodePreferred',
            'Install-NodePreferred',
            'Test-OpenClawPreferred',
            'Install-OpenClawPreferred',
            'Get-OllamaVersion',
            'Install-OllamaPreferred',
            'Install-ClawLocalPackage',
            'Invoke-LocalEnvironmentSetup',
            'Test-BootstrapFunctionContract'
        )

        foreach ($Name in $Required) {
            $FunctionNames | Should -Contain $Name -Because $Name
        }
    }

    It 'exécute le contrat interne avant le dry-run et avant toute installation' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $BootstrapPath = Join-Path $RepoRoot 'scripts\windows\00_bootstrap.ps1'
        $Content = (Get-Content -Raw -LiteralPath $BootstrapPath) -replace "`r`n", "`n"
        $ContractCall = $Content.IndexOf("Test-BootstrapFunctionContract`n`nif (-not `$IsWindows)")
        $DryRunBlock = $Content.IndexOf('if ($DryRun)')
        $FirstInstall = $Content.LastIndexOf("Install-PythonPreferred`nInstall-NodePreferred")

        $ContractCall | Should -BeGreaterOrEqual 0
        $DryRunBlock | Should -BeGreaterThan $ContractCall
        $FirstInstall | Should -BeGreaterThan $DryRunBlock
    }
}
