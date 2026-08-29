Set-StrictMode -Version Latest

function ConvertTo-UInt64MemoryByteCount {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    if ($Value -is [byte[]]) {
        if ($Value.Length -ge 8) {
            return [System.BitConverter]::ToUInt64($Value, 0)
        }
        if ($Value.Length -ge 4) {
            return [uint64][System.BitConverter]::ToUInt32($Value, 0)
        }
        return $null
    }

    if ($Value -is [int32] -and [int32]$Value -lt 0) {
        return [uint64][uint32][int32]$Value
    }

    try {
        return [uint64]$Value
    }
    catch {
        return $null
    }
}

function Get-RegistryVideoMemoryByteCount {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$AdapterName
    )

    $VideoRoot = 'HKLM:\SYSTEM\CurrentControlSet\Control\Video'
    if (-not (Test-Path -LiteralPath $VideoRoot)) {
        return $null
    }

    $AdapterKeys = @(Get-ChildItem -LiteralPath $VideoRoot -ErrorAction SilentlyContinue)
    foreach ($AdapterKey in $AdapterKeys) {
        $DeviceKeys = @(
            Get-ChildItem -LiteralPath $AdapterKey.PSPath -ErrorAction SilentlyContinue |
                Where-Object { $_.PSChildName -match '^\d{4}$' }
        )
        foreach ($DeviceKey in $DeviceKeys) {
            try {
                $Properties = Get-ItemProperty -LiteralPath $DeviceKey.PSPath -ErrorAction Stop
            }
            catch {
                continue
            }

            $Names = @()
            foreach ($PropertyName in @('DriverDesc', 'HardwareInformation.AdapterString')) {
                $Property = $Properties.PSObject.Properties[$PropertyName]
                if ($null -ne $Property -and $Property.Value) {
                    $Names += [string]$Property.Value
                }
            }

            $Matched = $false
            foreach ($Candidate in $Names) {
                if (
                    [string]::Equals(
                        $AdapterName,
                        $Candidate,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -or
                    $AdapterName.IndexOf(
                        $Candidate,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -ge 0 -or
                    $Candidate.IndexOf(
                        $AdapterName,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -ge 0
                ) {
                    $Matched = $true
                    break
                }
            }
            if (-not $Matched) {
                continue
            }

            $MemoryProperty = $Properties.PSObject.Properties['HardwareInformation.MemorySize']
            if ($null -eq $MemoryProperty) {
                continue
            }
            $ByteCount = ConvertTo-UInt64MemoryByteCount -Value $MemoryProperty.Value
            if ($null -ne $ByteCount -and $ByteCount -gt 0) {
                return $ByteCount
            }
        }
    }

    return $null
}

function Get-OpenClawGpuInventory {
    [CmdletBinding()]
    param()

    $Controllers = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue)
    $Inventory = @()

    foreach ($Controller in $Controllers) {
        $Name = [string]$Controller.Name
        $DriverVersion = [string]$Controller.DriverVersion
        $CimByteCount = $null
        $AdapterRamProperty = $Controller.PSObject.Properties['AdapterRAM']
        if ($null -ne $AdapterRamProperty -and $null -ne $AdapterRamProperty.Value) {
            $CimByteCount = ConvertTo-UInt64MemoryByteCount -Value $AdapterRamProperty.Value
        }

        $RegistryByteCount = Get-RegistryVideoMemoryByteCount -AdapterName $Name
        $VramGib = $null
        $VramSource = 'unavailable'
        $VramReliable = $false
        if ($null -ne $RegistryByteCount) {
            $VramGib = [math]::Round($RegistryByteCount / 1GB, 2)
            $VramSource = 'windows_registry_hardware_information'
            $VramReliable = $true
        }

        $CimGib = $null
        if ($null -ne $CimByteCount) {
            $CimGib = [math]::Round($CimByteCount / 1GB, 2)
        }

        $Inventory += [pscustomobject][ordered]@{
            name = $Name
            driver_version = $DriverVersion
            vram_bytes = $RegistryByteCount
            vram_gib = $VramGib
            vram_source = $VramSource
            vram_reliable = $VramReliable
            cim_adapter_ram_bytes = $CimByteCount
            cim_adapter_ram_gib = $CimGib
            cim_adapter_ram_informational_only = $true
        }
    }

    return $Inventory
}
