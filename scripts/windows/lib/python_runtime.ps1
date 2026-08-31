Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ClawLocalManagedPython {
    param([Parameter(Mandatory)][string]$PlatformRoot)

    $Python = Join-Path $PlatformRoot 'runtime\venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) {
        throw (
            "Runtime Python géré introuvable: $Python. " +
            'Exécutez .\menu.ps1 -Action install-core pour réparer le runtime.'
        )
    }

    & $Python -c 'import clawlocal, yaml' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw (
            "Runtime Python géré incomplet: $Python. " +
            'Le package clawlocal et PyYAML doivent être installés. ' +
            'Exécutez .\menu.ps1 -Action install-core.'
        )
    }
    return $Python
}

function Enable-ClawLocalManagedPython {
    param([Parameter(Mandatory)][string]$PlatformRoot)

    $Python = Get-ClawLocalManagedPython -PlatformRoot $PlatformRoot
    $Scripts = Split-Path -Parent $Python
    $Parts = @($env:PATH -split ';' | Where-Object { $_ })
    $Filtered = @($Parts | Where-Object { $_.TrimEnd('\\') -ne $Scripts.TrimEnd('\\') })
    $env:PATH = (@($Scripts) + $Filtered) -join ';'
    $env:OPENCLAW_LOCAL_PYTHON = $Python
    return $Python
}
