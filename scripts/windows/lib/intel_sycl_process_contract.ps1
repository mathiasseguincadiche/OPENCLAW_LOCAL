Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Redéfinit le stop du helper de base avec un contrat de sortie strict :
# aucune valeur de méthode .NET ne doit contaminer le success pipeline PowerShell.
function Stop-IntelSyclServer {
    [CmdletBinding(SupportsShouldProcess)]
    param([Parameter(Mandatory)][string]$StatePath)

    if (-not (Test-Path -LiteralPath $StatePath)) {
        return
    }
    if (-not $PSCmdlet.ShouldProcess(
        $StatePath,
        'Stop tracked Intel SYCL server and remove process state'
    )) {
        return
    }

    try {
        $State = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
        $Process = Get-Process -Id ([int]$State.pid) -ErrorAction SilentlyContinue
        if ($Process) {
            Stop-Process -Id $Process.Id -Force
            $null = $Process.WaitForExit(10000)
            Write-Host "OK  llama-server Intel SYCL arrêté (PID=$($Process.Id))."
        }
    }
    finally {
        Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
    }
}
