Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $HardwareHelper = Join-Path $RepoRoot 'scripts\windows\lib\hardware_inventory.ps1'
    . $HardwareHelper
}

Describe 'Inventaire matériel Windows' {
    It 'convertit une taille VRAM 64 bits sans troncature à 4 GiB' {
        $Expected = [uint64](12GB)
        $Bytes = [System.BitConverter]::GetBytes($Expected)
        $Actual = ConvertTo-UInt64MemoryByteCount -Value $Bytes
        $Actual | Should -Be $Expected
    }

    It 'ne présente plus AdapterRAM CIM comme source VRAM fiable' {
        $Audit = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'scripts\windows\01_audit_host.ps1'
        )
        $Inventory = Get-Content -Raw -LiteralPath (
            Join-Path $RepoRoot 'scripts\windows\06_collect_inventory.ps1'
        )
        $Audit | Should -Match 'Get-OpenClawGpuInventory'
        $Inventory | Should -Match 'Get-OpenClawGpuInventory'
        $Audit | Should -Match 'informatif uniquement'
    }
}
