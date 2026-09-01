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

    & $Python -c 'import yaml' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw (
            "Runtime Python géré incomplet: $Python. " +
            'PyYAML doit être installé. ' +
            'Exécutez .\menu.ps1 -Action install-core.'
        )
    }
    return $Python
}

function Get-ClawLocalRepoRoot {
    $Candidates = @()
    if ($env:OPENCLAW_LOCAL_REPO_ROOT) {
        $Candidates += [string]$env:OPENCLAW_LOCAL_REPO_ROOT
    }
    $Candidates += (Join-Path $PSScriptRoot '..\..\..')

    foreach ($Candidate in $Candidates) {
        if (-not (Test-Path -LiteralPath $Candidate)) {
            continue
        }
        $Resolved = (Resolve-Path -LiteralPath $Candidate).Path
        $SourcePackage = Join-Path $Resolved 'src\clawlocal'
        $ProjectFile = Join-Path $Resolved 'pyproject.toml'
        if (
            (Test-Path -LiteralPath $SourcePackage -PathType Container) -and
            (Test-Path -LiteralPath $ProjectFile -PathType Leaf)
        ) {
            return $Resolved
        }
    }

    throw (
        'Checkout OPENCLAW_LOCAL introuvable pour le runtime Python géré. ' +
        'OPENCLAW_LOCAL_REPO_ROOT doit pointer vers le dépôt courant.'
    )
}

function Enable-ClawLocalManagedPython {
    param([Parameter(Mandatory)][string]$PlatformRoot)

    $Python = Get-ClawLocalManagedPython -PlatformRoot $PlatformRoot
    $RepoRoot = Get-ClawLocalRepoRoot
    $SourceRoot = Join-Path $RepoRoot 'src'

    $Scripts = Split-Path -Parent $Python
    $PathParts = @($env:PATH -split ';' | Where-Object { $_ })
    $FilteredPath = @(
        $PathParts | Where-Object { $_.TrimEnd('\\') -ine $Scripts.TrimEnd('\\') }
    )
    $env:PATH = (@($Scripts) + $FilteredPath) -join ';'

    $PythonPathParts = @($env:PYTHONPATH -split ';' | Where-Object { $_ })
    $FilteredPythonPath = @(
        $PythonPathParts |
            Where-Object { $_.TrimEnd('\\') -ine $SourceRoot.TrimEnd('\\') }
    )
    $env:PYTHONPATH = (@($SourceRoot) + $FilteredPythonPath) -join ';'
    $env:OPENCLAW_LOCAL_PYTHON = $Python
    $env:OPENCLAW_LOCAL_REPO_ROOT = $RepoRoot

    & $Python -c @'
import pathlib
import sys
import yaml
import clawlocal

expected = pathlib.Path(sys.argv[1]).resolve()
actual = pathlib.Path(clawlocal.__file__).resolve()
if expected not in actual.parents:
    raise SystemExit(f"clawlocal hors checkout courant: {actual} (attendu sous {expected})")
'@ $SourceRoot *> $null
    if ($LASTEXITCODE -ne 0) {
        throw (
            "Runtime Python géré désynchronisé du checkout courant: $RepoRoot. " +
            'Le module clawlocal doit être importé depuis le dossier src du dépôt.'
        )
    }

    return $Python
}
