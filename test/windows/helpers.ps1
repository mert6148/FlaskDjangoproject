<#
    .SYNOPSIS
    Helper functions for Windows hardening Pester tests
#>

function Test-WindowsFirewall {
    <#
        .SYNOPSIS
        Check if Windows Firewall is properly configured
        
        .OUTPUTS
        PSCustomObject with firewall status
    #>
    
    $Profiles = @("Domain", "Public", "Private")
    $Results = @()
    
    foreach ($Profile in $Profiles) {
        $Firewall = Get-NetFirewallProfile -Name $Profile -ErrorAction SilentlyContinue
        $Results += [PSCustomObject]@{
            Profile = $Profile
            Enabled = $Firewall.Enabled
            DefaultInboundAction = $Firewall.DefaultInboundAction
            DefaultOutboundAction = $Firewall.DefaultOutboundAction
        }
    }
    
    return $Results
}

function Test-SMBv1Status {
    <#
        .SYNOPSIS
        Check if SMB v1 is disabled
        
        .OUTPUTS
        PSCustomObject with SMB v1 status
    #>
    
    $SMBv1 = Get-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -ErrorAction SilentlyContinue
    
    return [PSCustomObject]@{
        FeatureName = "SMB1Protocol"
        State = $SMBv1.State
        Installed = ($SMBv1.State -eq "Enabled")
        Vulnerable = ($SMBv1.State -eq "Enabled")
    }
}

function Test-WindowsDefender {
    <#
        .SYNOPSIS
        Check if Windows Defender is properly configured
        
        .OUTPUTS
        PSCustomObject with Defender status
    #>
    
    $DefenderService = Get-Service -Name WinDefend -ErrorAction SilentlyContinue
    $DefenderPreference = Get-MpPreference -ErrorAction SilentlyContinue
    
    return [PSCustomObject]@{
        ServiceRunning = ($DefenderService.Status -eq "Running")
        ServiceEnabled = ($DefenderService.StartType -in @("Automatic", "AutomaticDelayedStart"))
        RealtimeMonitoringEnabled = -not $DefenderPreference.DisableRealtimeMonitoring
        QuickScanEnabled = -not $DefenderPreference.DisableQuickScan
    }
}

function Test-FirewallRule {
    <#
        .SYNOPSIS
        Check if a specific firewall rule exists and is enabled
        
        .PARAMETER RuleName
        Display name of the firewall rule
        
        .PARAMETER Port
        Port number to check
        
        .OUTPUTS
        PSCustomObject with rule status
    #>
    
    param(
        [Parameter(Mandatory = $true)]
        [string]$RuleName,
        
        [int]$Port
    )
    
    $Rule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    
    $Result = [PSCustomObject]@{
        RuleName = $RuleName
        Port = $Port
        RuleExists = ($null -ne $Rule)
        RuleEnabled = ($Rule.Enabled -eq $true)
    }
    
    if ($Rule) {
        $Result | Add-Member -NotePropertyName Direction -NotePropertyValue $Rule.Direction
        $Result | Add-Member -NotePropertyName Action -NotePropertyValue $Rule.Action
    }
    
    return $Result
}

function Get-HardeningStatus {
    <#
        .SYNOPSIS
        Get overall Windows hardening status
        
        .OUTPUTS
        PSCustomObject with comprehensive hardening status
    #>
    
    $Firewall = Test-WindowsFirewall
    $SMBv1 = Test-SMBv1Status
    $Defender = Test-WindowsDefender
    
    $Status = [PSCustomObject]@{
        Timestamp = Get-Date
        Firewall = $Firewall
        SMBv1Disabled = -not $SMBv1.Vulnerable
        DefenderEnabled = $Defender.RealtimeMonitoringEnabled
        OverallSecure = (@($Firewall.Enabled) -contains $true) -and (-not $SMBv1.Vulnerable) -and ($Defender.RealtimeMonitoringEnabled)
    }
    
    return $Status
}

function Format-HardeningReport {
    <#
        .SYNOPSIS
        Format hardening status as readable report
        
        .PARAMETER Status
        Hardening status object from Get-HardeningStatus
        
        .OUTPUTS
        Formatted string report
    #>
    
    param(
        [Parameter(Mandatory = $true)]
        $Status
    )
    
    $Report = @"
Windows Hardening Status Report
================================
Generated: $($Status.Timestamp)

Firewall Status:
  - Domain Profile:    $($Status.Firewall[0].Enabled)
  - Public Profile:    $($Status.Firewall[1].Enabled)
  - Private Profile:   $($Status.Firewall[2].Enabled)

Security:
  - SMB v1 Disabled:   $($Status.SMBv1Disabled)
  - Defender Enabled:  $($Status.DefenderEnabled)

Overall Status:      $($Status.OverallSecure ? 'SECURE' : 'REVIEW NEEDED')
"@
    
    return $Report
}
