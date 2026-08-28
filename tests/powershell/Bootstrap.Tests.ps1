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
        $Bootstrap | Should -Match ([regex]::Escape("lib\bootstrap_openclaw.ps1"))
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

    It 'rend le runtime Node local prioritaire avant les scripts npm OpenClaw' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $OpenClawHelperPath = Join-Path $RepoRoot 'scripts\windows\lib\bootstrap_openclaw.ps1'
        $Content = (Get-Content -Raw -LiteralPath $OpenClawHelperPath) -replace "`r`n", "`n"

        $PathMutation = $Content.IndexOf("`$env:PATH = (@(`$NodeHome) + `$PathParts) -join ';'")
        $NodeResolution = $Content.IndexOf('Get-Command node.exe -ErrorAction SilentlyContinue')
        $NpmInstall = $Content.IndexOf('Invoke-NativeChecked -Command $Npm -Arguments @(')
        $AllowScripts = $Content.IndexOf("'--allow-scripts', 'openclaw'")

        $PathMutation | Should -BeGreaterOrEqual 0
        $NodeResolution | Should -BeGreaterThan $PathMutation
        $NpmInstall | Should -BeGreaterThan $NodeResolution
        $AllowScripts | Should -BeGreaterThan $NpmInstall
    }

    It 'ne valide OpenClaw qu'après écriture du marqueur de réussite' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $OpenClawHelperPath = Join-Path $RepoRoot 'scripts\windows\lib\bootstrap_openclaw.ps1'
        $Content = (Get-Content -Raw -LiteralPath $OpenClawHelperPath) -replace "`r`n", "`n"

        $MarkerCheck = $Content.IndexOf("'.openclaw-local-install.json'")
        $NpmInstall = $Content.IndexOf('Invoke-NativeChecked -Command $Npm -Arguments @(')
        $MarkerWrite = $Content.LastIndexOf("`$Marker = Join-Path `$NpmPrefix '.openclaw-local-install.json'")
        $FinalValidation = $Content.LastIndexOf('if (-not (Test-OpenClawPreferred -NpmPrefix $NpmPrefix))')

        $MarkerCheck | Should -BeGreaterOrEqual 0
        $MarkerWrite | Should -BeGreaterThan $NpmInstall
        $FinalValidation | Should -BeGreaterThan $MarkerWrite
    }

    It 'interdit les guillemets typographiques dans les sources PowerShell' {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $SmartQuotes = @(
            [char]0x2018,
            [char]0x2019,
            [char]0x201C,
            [char]0x201D
        )
        $Unsafe = @()
        foreach ($Script in Get-ChildItem -LiteralPath $RepoRoot -Recurse -Filter '*.ps1' -File) {
            $Content = Get-Content -Raw -LiteralPath $Script.FullName
            foreach ($Quote in $SmartQuotes) {
                if ($Content.Contains([string]$Quote)) {
                    $Unsafe += $Script.FullName
                    break
                }
            }
        }
        $Unsafe | Should -BeNullOrEmpty -Because ($Unsafe -join ', ')
    }
}
