Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-IntelSyclDeterministicSmoke {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Model,
        [int]$TimeoutSeconds = 300
    )

    $BodyObject = [ordered]@{
        model = $Model
        messages = @(
            [ordered]@{
                role = 'user'
                content = 'Réponds uniquement LOCAL_OK.'
            }
        )
        temperature = 0
        max_tokens = 32
        stream = $false
        chat_template_kwargs = [ordered]@{
            enable_thinking = $false
        }
    }
    $Body = $BodyObject | ConvertTo-Json -Depth 8 -Compress
    $Started = [DateTimeOffset]::UtcNow
    $Response = Invoke-RestMethod -Method Post `
        -Uri "$BaseUrl/chat/completions" `
        -ContentType 'application/json' `
        -Body $Body `
        -TimeoutSec $TimeoutSeconds
    $ElapsedMs = ([DateTimeOffset]::UtcNow - $Started).TotalMilliseconds

    $Choice = $Response.choices[0]
    $Message = $Choice.message
    $Content = [string]$Message.content
    $Reasoning = ''
    if ($Message.PSObject.Properties.Name -contains 'reasoning_content') {
        $Reasoning = [string]$Message.reasoning_content
    }
    if ($Content -notmatch 'LOCAL_OK') {
        throw (
            "Smoke Intel SYCL inattendu pour $Model. " +
            "content='$Content' reasoning_length=$($Reasoning.Length) " +
            "finish_reason=$([string]$Choice.finish_reason)"
        )
    }

    $Timings = $Response.timings
    return [pscustomobject]@{
        model = $Model
        wall_ms = [math]::Round($ElapsedMs, 1)
        prompt_tokens_per_second = if ($Timings) {
            $Timings.prompt_per_second
        }
        else {
            $null
        }
        tokens_per_second = if ($Timings) {
            $Timings.predicted_per_second
        }
        else {
            $null
        }
        predicted_tokens = if ($Timings) {
            $Timings.predicted_n
        }
        else {
            $null
        }
        finish_reason = [string]$Choice.finish_reason
        reasoning_content_present = -not [string]::IsNullOrWhiteSpace($Reasoning)
        thinking_disabled_for_smoke = $true
        ok = $true
    }
}
