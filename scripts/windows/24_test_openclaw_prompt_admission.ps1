[CmdletBinding()]
param(
    [string]$AgentId = 'chef-operations',
    [ValidateRange(30, 300)][int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PlatformRoot {
    if ($env:OPENCLAW_LOCAL_ROOT) {
        return $env:OPENCLAW_LOCAL_ROOT
    }
    if (Test-Path -LiteralPath 'E:\') {
        return 'E:\AI\OpenClawLocal'
    }
    return (Join-Path $env:LOCALAPPDATA 'OpenClawLocal')
}

function Get-OpenClawCommand([string]$PlatformRoot) {
    $Found = Get-Command openclaw -ErrorAction SilentlyContinue
    if ($Found) {
        return $Found.Source
    }
    $Managed = Join-Path $PlatformRoot 'runtime\npm-global\openclaw.cmd'
    if (Test-Path -LiteralPath $Managed) {
        return $Managed
    }
    throw 'OpenClaw absent. Exécutez install-core.'
}

function Get-AgentEntry {
    param(
        [Parameter(Mandatory)]$Config,
        [Parameter(Mandatory)][string]$Id
    )
    $Entries = $Config.agents.PSObject.Properties['entries']
    if ($Entries -and $Entries.Value) {
        $Entry = $Entries.Value.PSObject.Properties[$Id]
        if ($Entry -and $Entry.Value) {
            return $Entry.Value
        }
    }
    $List = $Config.agents.PSObject.Properties['list']
    if ($List -and $List.Value) {
        $Entry = @($List.Value | Where-Object { [string]$_.id -eq $Id }) | Select-Object -First 1
        if ($Entry) {
            return $Entry
        }
    }
    throw "Agent absent de la configuration OpenClaw: $Id"
}

function Get-VisibleText {
    param([Parameter(Mandatory)]$Payload)

    $Result = $Payload.PSObject.Properties['result']
    if ($Result -and $Result.Value) {
        $Meta = $Result.Value.PSObject.Properties['meta']
        if ($Meta -and $Meta.Value) {
            $Visible = $Meta.Value.PSObject.Properties['finalAssistantVisibleText']
            if ($Visible -and -not [string]::IsNullOrWhiteSpace([string]$Visible.Value)) {
                return [string]$Visible.Value
            }
        }
    }
    $Final = $Payload.PSObject.Properties['final']
    if ($Final -and -not [string]::IsNullOrWhiteSpace([string]$Final.Value)) {
        return [string]$Final.Value
    }
    $Payloads = $Payload.PSObject.Properties['payloads']
    if ($Payloads) {
        $Texts = @(
            $Payloads.Value | ForEach-Object {
                $Text = $_.PSObject.Properties['text']
                if ($Text -and -not [string]::IsNullOrWhiteSpace([string]$Text.Value)) {
                    [string]$Text.Value
                }
            }
        )
        if ($Texts.Count -gt 0) {
            return ($Texts -join "`n")
        }
    }
    return ''
}

function Write-PromptBudgetSummary {
    param([Parameter(Mandatory)]$Payload)

    $Result = $Payload.PSObject.Properties['result']
    if (-not $Result -or -not $Result.Value) {
        return
    }
    $Meta = $Result.Value.PSObject.Properties['meta']
    if (-not $Meta -or -not $Meta.Value) {
        return
    }
    $ReportProperty = $Meta.Value.PSObject.Properties['systemPromptReport']
    if (-not $ReportProperty -or -not $ReportProperty.Value) {
        return
    }

    $Report = $ReportProperty.Value
    $SystemPrompt = $Report.PSObject.Properties['systemPrompt']
    $Tools = $Report.PSObject.Properties['tools']
    $Skills = $Report.PSObject.Properties['skills']

    if ($SystemPrompt -and $SystemPrompt.Value) {
        $Chars = $SystemPrompt.Value.PSObject.Properties['chars']
        if ($Chars) {
            Write-Host "PROMPT_ADMISSION_SYSTEM_CHARS=$($Chars.Value)"
        }
    }
    if ($Tools -and $Tools.Value) {
        foreach ($Name in @('listChars', 'schemaChars')) {
            $Value = $Tools.Value.PSObject.Properties[$Name]
            if ($Value) {
                Write-Host "PROMPT_ADMISSION_TOOLS_$($Name.ToUpperInvariant())=$($Value.Value)"
            }
        }
    }
    if ($Skills -and $Skills.Value) {
        $Chars = $Skills.Value.PSObject.Properties['promptChars']
        if ($Chars) {
            Write-Host "PROMPT_ADMISSION_SKILLS_CHARS=$($Chars.Value)"
        }
    }
}

$PlatformRoot = Get-PlatformRoot
$StateDir = Join-Path $PlatformRoot 'state'
$ProofsRoot = Join-Path $PlatformRoot 'proofs'
$ConfigPath = Join-Path $StateDir 'openclaw.json'
$OpenClaw = Get-OpenClawCommand $PlatformRoot

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw 'Configuration OpenClaw absente avant le contrôle d admission.'
}
New-Item -ItemType Directory -Path $ProofsRoot -Force | Out-Null

$env:OPENCLAW_STATE_DIR = $StateDir
$env:OLLAMA_API_KEY = 'ollama-local'
$env:INTEL_SYCL_API_KEY = 'intel-sycl-local'
$env:INTEL_VULKAN_API_KEY = 'intel-vulkan-local'
$env:OPENCLAW_LOCAL_CLOUD_ENABLED = 'false'

$Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
$Agent = Get-AgentEntry -Config $Config -Id $AgentId
$ModelRef = [string]$Agent.model.primary
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$EvidencePath = Join-Path $ProofsRoot "openclaw_prompt_admission_$Stamp.json"
$SessionKey = "configure-admission-$Stamp-$AgentId"
$Expected = "PROMPT_ADMISSION_OK $AgentId"
$Prompt = "N'utilise aucun outil. Réponds immédiatement en une ligne avec exactement: $Expected"

Write-Host "ADMISSION  Agent=$AgentId modèle=$ModelRef timeout=${TimeoutSeconds}s"
$Output = & $OpenClaw 'agent' '--agent' $AgentId `
    '--session-key' $SessionKey '--message' $Prompt '--thinking' 'off' `
    '--timeout' ([string]$TimeoutSeconds) '--json' 2>&1
$ExitCode = $LASTEXITCODE
$Text = ($Output | Out-String).Trim()
if ($ExitCode -ne 0) {
    [ordered]@{
        schema_version = '1.0.0'
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
        agent = $AgentId
        model_ref = $ModelRef
        exit_code = $ExitCode
        raw_output = $Text
    } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
    Write-Host "PROMPT_ADMISSION_EVIDENCE=$EvidencePath"
    throw "Contrôle d admission OpenClaw en échec processus (code $ExitCode)."
}

try {
    $Payload = $Text | ConvertFrom-Json
}
catch {
    Set-Content -LiteralPath $EvidencePath -Value $Text -Encoding utf8
    Write-Host "PROMPT_ADMISSION_EVIDENCE=$EvidencePath"
    throw 'Contrôle d admission OpenClaw: sortie JSON invalide.'
}

$Payload | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
Write-Host "PROMPT_ADMISSION_EVIDENCE=$EvidencePath"
Write-PromptBudgetSummary -Payload $Payload

$Result = $Payload.PSObject.Properties['result']
if (-not $Result -or -not $Result.Value) {
    throw 'Contrôle d admission OpenClaw sans résultat agent.'
}
$Meta = $Result.Value.PSObject.Properties['meta']
if (-not $Meta -or -not $Meta.Value) {
    throw 'Contrôle d admission OpenClaw sans métadonnées agent.'
}
$ErrorProperty = $Meta.Value.PSObject.Properties['error']
if ($ErrorProperty -and $ErrorProperty.Value) {
    $KindProperty = $ErrorProperty.Value.PSObject.Properties['kind']
    $MessageProperty = $ErrorProperty.Value.PSObject.Properties['message']
    $Kind = if ($KindProperty) { [string]$KindProperty.Value } else { '' }
    $Message = if ($MessageProperty) { [string]$MessageProperty.Value } else { '' }
    if (-not [string]::IsNullOrWhiteSpace($Kind) -or -not [string]::IsNullOrWhiteSpace($Message)) {
        throw "Contrôle d admission OpenClaw refusé: kind=$Kind message=$Message preuve=$EvidencePath"
    }
}

$Visible = (Get-VisibleText -Payload $Payload).Trim()
if ($Visible -ne $Expected) {
    throw "Contrôle d admission OpenClaw réponse inattendue. Attendu='$Expected' Reçu='$Visible' preuve=$EvidencePath"
}

Write-Host "OK  Admission prompt OpenClaw validée: $AgentId -> $ModelRef"
exit 0
