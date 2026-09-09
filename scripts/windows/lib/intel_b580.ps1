Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-OpenClawLocalPlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Get-IntelArcB580DriverInfo {
    $Adapter = Get-CimInstance Win32_VideoController -ErrorAction Stop |
        Where-Object { [string]$_.Name -match '(?i)Intel.*Arc.*B580|Arc.*B580.*Intel' } |
        Select-Object -First 1
    if (-not $Adapter) {
        throw 'Intel Arc B580 absente de Win32_VideoController.'
    }
    return [pscustomobject]@{
        name = [string]$Adapter.Name
        driver_version = [string]$Adapter.DriverVersion
        pnp_device_id = [string]$Adapter.PNPDeviceID
    }
}

function Resolve-OllamaGgufPath {
    param([Parameter(Mandatory)][string]$Model)

    $Output = @(& ollama show $Model --modelfile 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de lire le Modelfile Ollama pour $Model."
    }
    $FromLine = $Output |
        Where-Object { [string]$_ -match '^\s*FROM\s+' } |
        Select-Object -First 1
    if (-not $FromLine) {
        throw "Ligne FROM absente du Modelfile Ollama pour $Model."
    }
    $Raw = ([string]$FromLine -replace '^\s*FROM\s+', '').Trim().Trim('"')
    if (-not (Test-Path -LiteralPath $Raw)) {
        throw (
            "Le modèle Ollama $Model ne référence pas un blob GGUF local " +
            "exploitable: $Raw"
        )
    }
    return (Resolve-Path -LiteralPath $Raw).Path
}
