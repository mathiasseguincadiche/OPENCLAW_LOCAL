[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ConfigPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    return
}

try {
    $Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
}
catch {
    throw "Configuration OpenClaw illisible avant migration: $ConfigPath. Détail: $($_.Exception.Message)"
}

$Changes = [System.Collections.Generic.List[string]]::new()

$MetaProperty = $Config.PSObject.Properties['meta']
if ($MetaProperty -and $MetaProperty.Value) {
    $Meta = $MetaProperty.Value
    if ($Meta.PSObject.Properties['lastTouchedAt']) {
        $Meta.PSObject.Properties.Remove('lastTouchedAt')
        $Changes.Add('meta.lastTouchedAt')
    }
}

$AgentsProperty = $Config.PSObject.Properties['agents']
if ($AgentsProperty -and $AgentsProperty.Value) {
    $Agents = $AgentsProperty.Value
    $DefaultsProperty = $Agents.PSObject.Properties['defaults']
    if ($DefaultsProperty -and $DefaultsProperty.Value) {
        $Defaults = $DefaultsProperty.Value

        $LegacyPdfProperty = $Defaults.PSObject.Properties['pdfMaxBytesMb']
        if ($LegacyPdfProperty) {
            if (-not $Defaults.PSObject.Properties['pdfMaxMb']) {
                $Defaults | Add-Member -NotePropertyName 'pdfMaxMb' `
                    -NotePropertyValue $LegacyPdfProperty.Value
            }
            $Defaults.PSObject.Properties.Remove('pdfMaxBytesMb')
            $Changes.Add('agents.defaults.pdfMaxBytesMb->pdfMaxMb')
        }

        $CompactionProperty = $Defaults.PSObject.Properties['compaction']
        if ($CompactionProperty -and $CompactionProperty.Value) {
            $Compaction = $CompactionProperty.Value
            foreach ($RetiredKey in @('reserveTokens', 'reserveTokensFloor')) {
                if ($Compaction.PSObject.Properties[$RetiredKey]) {
                    $Compaction.PSObject.Properties.Remove($RetiredKey)
                    $Changes.Add("agents.defaults.compaction.$RetiredKey")
                }
            }
            if (@($Compaction.PSObject.Properties).Count -eq 0) {
                $Defaults.PSObject.Properties.Remove('compaction')
            }
        }
    }
}

if ($Changes.Count -eq 0) {
    Write-Host 'OK  État OpenClaw: aucune clé legacy 2026.7.x à migrer.'
    return
}

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$BackupPath = "$ConfigPath.pre-2026.8.2-$Stamp.bak"
$TempPath = "$ConfigPath.migrating-$PID.tmp"

Copy-Item -LiteralPath $ConfigPath -Destination $BackupPath -Force
try {
    $Config | ConvertTo-Json -Depth 100 |
        Set-Content -LiteralPath $TempPath -Encoding utf8
    $null = Get-Content -Raw -LiteralPath $TempPath | ConvertFrom-Json
    Move-Item -LiteralPath $TempPath -Destination $ConfigPath -Force
}
catch {
    Remove-Item -LiteralPath $TempPath -Force -ErrorAction SilentlyContinue
    throw "Migration legacy OpenClaw interrompue; original conservé dans $BackupPath. Détail: $($_.Exception.Message)"
}

Write-Host "OK  État OpenClaw pré-migré avant démarrage CLI: $($Changes -join ', ')."
Write-Host "OPENCLAW_STATE_BACKUP=$BackupPath"
