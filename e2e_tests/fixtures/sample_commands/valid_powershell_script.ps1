<#
.SYNOPSIS
    Queries system uptime and diagnostic hardware metrics.
.DESCRIPTION
    Use when diagnosing system lag, inspecting background thermal throttle,
    or verifying host reboot schedules.
.PARAMETER IncludeDisks
    If specified, queries per-volume free disk capacity.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$IncludeDisks
)

$uptime = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
Write-Output "Uptime: $($uptime.TotalHours) hours"
