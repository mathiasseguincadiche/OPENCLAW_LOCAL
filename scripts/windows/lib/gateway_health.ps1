Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-OpenClawObjectProperty {
    param(
        [AllowNull()][object]$InputObject,
        [Parameter(Mandatory)][string]$Name
    )

    if ($null -eq $InputObject) {
        return $null
    }
    $Property = $InputObject.PSObject.Properties[$Name]
    if ($null -eq $Property) {
        return $null
    }
    return $Property.Value
}

function Protect-OpenClawDiagnosticText {
    param([AllowNull()][string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $Text
    }

    $Protected = $Text -replace '(?i)Bearer\s+[^\s,;]+', 'Bearer <redacted>'
    $Protected = $Protected -replace '(?i)(token|api[_-]?key|authorization|password|secret)(\s*[:=]\s*)[^\s,;"'']+', '$1$2<redacted>'
    return $Protected
}

function Invoke-OpenClawCommandCapture {
    param(
        [Parameter(Mandatory)][string]$OpenClaw,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    $Output = & $OpenClaw @Arguments 2>&1
    $ExitCode = $LASTEXITCODE
    $Text = ($Output | Out-String).Trim()
    $Json = $null
    if (-not [string]::IsNullOrWhiteSpace($Text)) {
        try {
            $Json = $Text | ConvertFrom-Json
        }
        catch {
            $Json = $null
        }
    }

    return [pscustomobject]@{
        exit_code = [int]$ExitCode
        text = $Text
        json = $Json
    }
}

function ConvertTo-OpenClawGatewayProbeSnapshot {
    param([Parameter(Mandatory)][object]$Probe)

    $Json = Get-OpenClawObjectProperty -InputObject $Probe -Name 'json'
    $Service = Get-OpenClawObjectProperty -InputObject $Json -Name 'service'
    $Runtime = Get-OpenClawObjectProperty -InputObject $Service -Name 'runtime'
    $Port = Get-OpenClawObjectProperty -InputObject $Json -Name 'port'
    $Rpc = Get-OpenClawObjectProperty -InputObject $Json -Name 'rpc'
    $Health = Get-OpenClawObjectProperty -InputObject $Json -Name 'health'

    $RuntimeStatus = [string](Get-OpenClawObjectProperty -InputObject $Runtime -Name 'status')
    $PortStatus = [string](Get-OpenClawObjectProperty -InputObject $Port -Name 'status')
    $PortNumber = Get-OpenClawObjectProperty -InputObject $Port -Name 'port'
    $RpcOk = Get-OpenClawObjectProperty -InputObject $Rpc -Name 'ok'
    $RpcError = [string](Get-OpenClawObjectProperty -InputObject $Rpc -Name 'error')
    $Healthy = Get-OpenClawObjectProperty -InputObject $Health -Name 'healthy'
    $ExitCode = [int](Get-OpenClawObjectProperty -InputObject $Probe -Name 'exit_code')

    $IsReady = ($ExitCode -eq 0 -and $RpcOk -eq $true)
    return [pscustomobject]@{
        ready = [bool]$IsReady
        exit_code = $ExitCode
        runtime_status = $RuntimeStatus
        port = $PortNumber
        port_status = $PortStatus
        rpc_ok = $RpcOk
        rpc_error = $RpcError
        healthy = $Healthy
    }
}

function Get-OpenClawGatewayFailureClass {
    param([Parameter(Mandatory)][object]$Snapshot)

    if ([bool]$Snapshot.ready) {
        return 'READY'
    }
    if ($Snapshot.runtime_status -eq 'running' -and $Snapshot.port_status -eq 'free') {
        return 'RUNTIME_DETECTED_NO_LISTENER'
    }
    if ($Snapshot.runtime_status -eq 'running' -and $Snapshot.rpc_ok -eq $false) {
        return 'RPC_UNHEALTHY'
    }
    if ($Snapshot.port_status -eq 'free' -and $Snapshot.runtime_status -ne 'running') {
        return 'SERVICE_STOPPED_OR_EXITED'
    }
    if ($Snapshot.exit_code -ne 0 -and [string]::IsNullOrWhiteSpace($Snapshot.runtime_status)) {
        return 'STATUS_PROBE_FAILED'
    }
    return 'NOT_READY'
}

function Wait-OpenClawGatewayReady {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$OpenClaw,
        [ValidateRange(5, 300)][int]$TimeoutSeconds = 90,
        [ValidateRange(1, 10000)][int]$PollIntervalMilliseconds = 2000
    )

    $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $Attempts = 0
    $LastSnapshot = $null
    $LastProgressBucket = -1

    while ($Stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $Attempts++
        $Probe = Invoke-OpenClawCommandCapture -OpenClaw $OpenClaw -Arguments @(
            'gateway', 'status', '--require-rpc', '--json'
        )
        $LastSnapshot = ConvertTo-OpenClawGatewayProbeSnapshot -Probe $Probe

        if ($LastSnapshot.ready) {
            $Stopwatch.Stop()
            Write-Host "OK  Gateway OpenClaw prêt en $([math]::Round($Stopwatch.Elapsed.TotalSeconds, 1)) s ($Attempts tentative(s))."
            return [pscustomobject]@{
                ready = $true
                attempts = $Attempts
                elapsed_seconds = [math]::Round($Stopwatch.Elapsed.TotalSeconds, 3)
                failure_class = 'READY'
                last_snapshot = $LastSnapshot
            }
        }

        $ProgressBucket = [math]::Floor($Stopwatch.Elapsed.TotalSeconds / 10)
        if ($Attempts -eq 1 -or $ProgressBucket -gt $LastProgressBucket) {
            $LastProgressBucket = $ProgressBucket
            $Class = Get-OpenClawGatewayFailureClass -Snapshot $LastSnapshot
            Write-Host "ATTENTE Gateway: $Class (runtime=$($LastSnapshot.runtime_status), port=$($LastSnapshot.port_status), rpc=$($LastSnapshot.rpc_ok))."
        }

        if ($Stopwatch.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
            break
        }
        Start-Sleep -Milliseconds $PollIntervalMilliseconds
    }

    $Stopwatch.Stop()
    if ($null -eq $LastSnapshot) {
        $LastSnapshot = [pscustomobject]@{
            ready = $false
            exit_code = -1
            runtime_status = ''
            port = $null
            port_status = ''
            rpc_ok = $null
            rpc_error = 'Aucune sonde Gateway exécutée.'
            healthy = $false
        }
    }
    $FailureClass = Get-OpenClawGatewayFailureClass -Snapshot $LastSnapshot
    return [pscustomobject]@{
        ready = $false
        attempts = $Attempts
        elapsed_seconds = [math]::Round($Stopwatch.Elapsed.TotalSeconds, 3)
        failure_class = $FailureClass
        last_snapshot = $LastSnapshot
    }
}

function Get-OpenClawScheduledTaskEvidence {
    $Evidence = @()
    if (-not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) {
        return $Evidence
    }

    try {
        $Tasks = @(
            Get-ScheduledTask -ErrorAction Stop |
                Where-Object { $_.TaskName -like '*OpenClaw*' }
        )
        foreach ($Task in $Tasks) {
            $Info = $null
            try {
                $Info = Get-ScheduledTaskInfo -TaskName $Task.TaskName `
                    -TaskPath $Task.TaskPath -ErrorAction Stop
            }
            catch {
                $Info = $null
            }
            $Evidence += [pscustomobject]@{
                task_name = $Task.TaskName
                task_path = $Task.TaskPath
                state = [string]$Task.State
                last_run_time = if ($Info) { $Info.LastRunTime } else { $null }
                last_task_result = if ($Info) { $Info.LastTaskResult } else { $null }
                next_run_time = if ($Info) { $Info.NextRunTime } else { $null }
            }
        }
    }
    catch {
        $Evidence += [pscustomobject]@{
            error = $_.Exception.Message
        }
    }
    return $Evidence
}

function Get-OpenClawTcpEvidence {
    param([int]$Port = 18789)

    if (-not (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) {
        return @()
    }
    try {
        return @(
            Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
                Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
        )
    }
    catch {
        return @([pscustomobject]@{ error = $_.Exception.Message })
    }
}

function Get-OpenClawRuntimeLogEvidence {
    param([AllowNull()][string]$PreferredPath)

    $LogPath = $PreferredPath
    if ([string]::IsNullOrWhiteSpace($LogPath) -or -not (Test-Path -LiteralPath $LogPath)) {
        $TempOpenClaw = Join-Path ([System.IO.Path]::GetTempPath()) 'openclaw'
        if (Test-Path -LiteralPath $TempOpenClaw) {
            $Latest = Get-ChildItem -LiteralPath $TempOpenClaw -Filter 'openclaw-*.log' -File `
                -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($Latest) {
                $LogPath = $Latest.FullName
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($LogPath) -or -not (Test-Path -LiteralPath $LogPath)) {
        return [pscustomobject]@{
            path = $null
            tail = $null
        }
    }

    try {
        $Tail = (Get-Content -LiteralPath $LogPath -Tail 200 -ErrorAction Stop | Out-String).Trim()
        return [pscustomobject]@{
            path = $LogPath
            tail = Protect-OpenClawDiagnosticText -Text $Tail
        }
    }
    catch {
        return [pscustomobject]@{
            path = $LogPath
            tail = "Lecture impossible: $($_.Exception.Message)"
        }
    }
}

function Write-OpenClawGatewayDiagnostic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$OpenClaw,
        [Parameter(Mandatory)][string]$PlatformRoot,
        [Parameter(Mandatory)][object]$Readiness
    )

    $ProofRoot = Join-Path $PlatformRoot 'proofs\gateway'
    New-Item -ItemType Directory -Path $ProofRoot -Force | Out-Null

    $Deep = Invoke-OpenClawCommandCapture -OpenClaw $OpenClaw -Arguments @(
        'gateway', 'status', '--deep', '--json'
    )
    $Config = Invoke-OpenClawCommandCapture -OpenClaw $OpenClaw -Arguments @(
        'config', 'validate', '--json'
    )
    $Plugins = Invoke-OpenClawCommandCapture -OpenClaw $OpenClaw -Arguments @(
        'plugins', 'list', '--json'
    )
    $Parallel = Invoke-OpenClawCommandCapture -OpenClaw $OpenClaw -Arguments @(
        'plugins', 'inspect', 'parallel', '--runtime', '--json'
    )

    $DeepJson = Get-OpenClawObjectProperty -InputObject $Deep -Name 'json'
    $PreferredLogPath = [string](Get-OpenClawObjectProperty -InputObject $DeepJson -Name 'logFile')
    $Port = 18789
    if ($Readiness.last_snapshot.port) {
        $Port = [int]$Readiness.last_snapshot.port
    }

    $Payload = [ordered]@{
        schema_version = '1.0.0'
        timestamp_utc = [DateTimeOffset]::UtcNow.ToString('o')
        failure_class = [string]$Readiness.failure_class
        readiness = $Readiness
        gateway_status_deep = [ordered]@{
            exit_code = $Deep.exit_code
            text = Protect-OpenClawDiagnosticText -Text $Deep.text
        }
        config_validate = [ordered]@{
            exit_code = $Config.exit_code
            text = Protect-OpenClawDiagnosticText -Text $Config.text
        }
        plugins = [ordered]@{
            exit_code = $Plugins.exit_code
            text = Protect-OpenClawDiagnosticText -Text $Plugins.text
        }
        parallel_runtime = [ordered]@{
            exit_code = $Parallel.exit_code
            text = Protect-OpenClawDiagnosticText -Text $Parallel.text
        }
        scheduled_task = @(Get-OpenClawScheduledTaskEvidence)
        tcp = @(Get-OpenClawTcpEvidence -Port $Port)
        runtime_log = Get-OpenClawRuntimeLogEvidence -PreferredPath $PreferredLogPath
    }

    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
    $Path = Join-Path $ProofRoot "gateway_diagnostic_$Stamp.json"
    $Payload | ConvertTo-Json -Depth 50 |
        Set-Content -LiteralPath $Path -Encoding utf8
    return $Path
}
