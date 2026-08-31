Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-IntelSyclRouterBaseUrl {
    param([Parameter(Mandatory)][string]$BaseUrl)

    return ($BaseUrl.TrimEnd('/') -replace '/v1$', '')
}

function Get-IntelSyclRouterModels {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [int]$TimeoutSeconds = 10
    )

    $RouterBaseUrl = Get-IntelSyclRouterBaseUrl -BaseUrl $BaseUrl
    return Invoke-RestMethod -Method Get `
        -Uri "$RouterBaseUrl/models?reload=1" `
        -TimeoutSec $TimeoutSeconds
}

function Wait-IntelSyclModelUnloaded {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Model,
        [int]$TimeoutSeconds = 60
    )

    $Deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $Inventory = Get-IntelSyclRouterModels -BaseUrl $BaseUrl -TimeoutSeconds 10
        $Entry = @(
            $Inventory.data |
                Where-Object { [string]$_.id -ieq $Model }
        ) | Select-Object -First 1
        if (-not $Entry) {
            return $true
        }
        $Status = [string]$Entry.status.value
        if ($Status -eq 'unloaded') {
            return $true
        }
        Start-Sleep -Milliseconds 500
    } while ([DateTimeOffset]::UtcNow -lt $Deadline)

    throw "Le modèle Intel SYCL $Model n'est pas revenu à l'état unloaded après $TimeoutSeconds s."
}

function Unload-IntelSyclModel {
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Model,
        [int]$TimeoutSeconds = 60
    )

    $RouterBaseUrl = Get-IntelSyclRouterBaseUrl -BaseUrl $BaseUrl
    $Body = @{ model = $Model } | ConvertTo-Json -Compress
    $Response = Invoke-RestMethod -Method Post `
        -Uri "$RouterBaseUrl/models/unload" `
        -ContentType 'application/json' `
        -Body $Body `
        -TimeoutSec 30
    if ($Response.PSObject.Properties.Name -contains 'success') {
        if (-not [bool]$Response.success) {
            throw "Le routeur Intel SYCL a refusé l'unload du modèle $Model."
        }
    }
    $null = Wait-IntelSyclModelUnloaded `
        -BaseUrl $BaseUrl -Model $Model -TimeoutSeconds $TimeoutSeconds
    Write-Host "OK  Intel SYCL modèle déchargé avant switch: $Model"
}
