[CmdletBinding()]
param(
    [switch]$DryRun,
    [string[]]$Models = @('qwen3.5:9b', 'gemma4')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ResultsDir = Join-Path $RepoRoot 'benchmarks\results'

$Prompts = @(
    'Résume en trois points les avantages d''un déploiement local-first.',
    'Écris un fragment YAML CI/CD minimal et valide contenant un job de test.'
)

if ($DryRun) {
    Write-Host "[DRY-RUN] Benchmark de $($Models -join ', ') ; résultats dans $ResultsDir"
    exit 0
}

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$Rows = @()

foreach ($Model in $Models) {
    foreach ($Prompt in $Prompts) {
        $Watch = [System.Diagnostics.Stopwatch]::StartNew()
        $Output = (& ollama run $Model $Prompt | Out-String).Trim()
        $ExitCode = $LASTEXITCODE
        $Watch.Stop()

        $Rows += [pscustomobject]@{
            model = $Model
            seconds = [math]::Round($Watch.Elapsed.TotalSeconds, 3)
            exit_code = $ExitCode
            output_chars = $Output.Length
            prompt = $Prompt
        }
    }
}

$Gpu = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
    Select-Object Name, DriverVersion
$Payload = [pscustomobject]@{
    timestamp = (Get-Date).ToString('o')
    note = 'Latence murale simple; ne pas interpréter comme tokens/s.'
    gpu = $Gpu
    results = $Rows
}

$Path = Join-Path $ResultsDir ("benchmark_{0}.json" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$Payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Path -Encoding UTF8
Write-Host "Benchmark enregistré : $Path"
