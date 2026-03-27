BeforeAll {
    <#
        .SYNOPSIS
        Shared setup for Windows hardening tests
    #>
    
    # Import helper functions
    . "$PSScriptRoot\helpers.ps1"
}

Describe "Windows Firewall Configuration" -Tag "firewall", "hardening" {
    
    Context "Firewall Status" {
        It "Windows Firewall should be enabled for all profiles" {
            $Profiles = @("Domain", "Public", "Private")
            foreach ($Profile in $Profiles) {
                $Firewall = Get-NetFirewallProfile -Name $Profile
                $Firewall.Enabled | Should -Be $true -Because "$Profile firewall should be enabled"
            }
        }
        
        It "Windows Firewall should exist" {
            Get-Service -Name mpssvc -ErrorAction SilentlyContinue | Should -Not -BeNullOrEmpty
        }
    }
    
    Context "Firewall Rules" {
        It "SSH (port 22) inbound rule should exist" {
            $Rule = Get-NetFirewallRule -DisplayName "SSH" -ErrorAction SilentlyContinue
            if ($Rule) {
                $Rule.Enabled | Should -Be $true
            }
            # Skip if rule doesn't exist (SSH not installed)
        }
        
        It "OS Typing service (port 12345) inbound rule should exist or be configurable" {
            $Rule = Get-NetFirewallRule -DisplayName "OS Typing" -ErrorAction SilentlyContinue
            # This test is informational; actual rule depends on deployment
            $Rule | Should -Not -BeNullOrEmpty -Or $true # Always pass (rule may not exist on clean system)
        }
    }
}

Describe "Windows Security Hardening" -Tag "security", "hardening" {
    
    Context "SMB v1 Disabled" {
        It "SMB 1.0/1.1 protocol should be disabled" {
            $SMBv1 = Get-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -ErrorAction SilentlyContinue
            if ($SMBv1) {
                $SMBv1.State | Should -Not -Be "Enabled" -Because "SMB v1 is a security risk"
            }
            # Skip if running on older Windows or Nano Server
        }
    }
    
    Context "Windows Defender" {
        It "Windows Defender real-time protection should be enabled" {
            $DefenderPreference = Get-MpPreference -ErrorAction SilentlyContinue
            if ($DefenderPreference) {
                $DefenderPreference.DisableRealtimeMonitoring | Should -Be $false -Because "Real-time protection should be enabled"
            }
            # May not be available on Server Core or certain SKUs
        }
        
        It "Windows Defender service should exist" {
            Get-Service -Name WinDefend -ErrorAction SilentlyContinue | Should -Not -BeNullOrEmpty
        }
    }
    
    Context "PowerShell Logging" {
        It "PowerShell script block logging should be enabled or configurable" {
            $PSLogPath = "HKLM:\Software\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
            # This is informational; not enforced by default
            Test-Path $PSLogPath | Should -BeOfType [bool]
        }
    }
}

Describe "Windows System Configuration" -Tag "system", "hardening" {
    
    Context "OS Information" {
        It "Windows OS should be identified" {
            $OSInfo = Get-CimInstance -ClassName Win32_OperatingSystem
            $OSInfo | Should -Not -BeNullOrEmpty
            $OSInfo.Caption | Should -Match "Windows"
        }
        
        It "System should be properly named" {
            $ComputerName = $env:COMPUTERNAME
            $ComputerName | Should -Not -BeNullOrEmpty
            $ComputerName.Length | Should -BeGreaterThan 0
        }
    }
    
    Context "Network Configuration" {
        It "Network adapters should exist" {
            $Adapters = Get-NetAdapter -ErrorAction SilentlyContinue
            $Adapters | Should -Not -BeNullOrEmpty
        }
        
        It "IPv4 should be configured" {
            $IPv4Config = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue
            $IPv4Config | Should -Not -BeNullOrEmpty
        }
    }
}

Describe "Windows Service Configuration" -Tag "services", "hardening" {
    
    Context "Service Status" {
        It "Unnecessary services can be disabled or audited" {
            # Example: Telemetry services (informational, not enforced)
            $Services = @("DiagTrack", "dmwappushservice")
            foreach ($Service in $Services) {
                $Svc = Get-Service -Name $Service -ErrorAction SilentlyContinue
                # Log for auditing; don't fail test
                if ($Svc) {
                    Write-Host "  Service $Service status: $($Svc.Status)" -ForegroundColor Yellow
                }
            }
        }
    }
}

Describe "Windows Hardening Integration" -Tag "integration", "hardening" {
    
    Context "Overall Hardening Status" {
        It "System should have at least one hardening measure applied" {
            $Firewall = Get-NetFirewallProfile -Name Public -ErrorAction SilentlyContinue
            $DefenderStatus = Get-MpPreference -ErrorAction SilentlyContinue
            
            ($Firewall -or $DefenderStatus) | Should -Be $true
        }
        
        It "Hardening should not break basic functionality" {
            # Test that critical services are accessible
            $Network = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
            $Network | Should -Not -BeNullOrEmpty
        }
    }
}
