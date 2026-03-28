# Windows Pester Tests Configuration and Documentation

## Overview

This directory contains **Pester** tests for Windows hardening verification in the **os_typing** project.

Pester is PowerShell's testing and mocking framework, ideal for validating:
- Windows Firewall configuration
- SMB v1 disabled
- Windows Defender enabled
- Firewall rules and service ports
- OS and network configuration

## Files

- **HardeningTests.ps1** — Main Pester test suite (Describe/Context/It blocks)
- **helpers.ps1** — Helper functions for firewall, Defender, SMB v1 checks
- **Run-Tests.ps1** — Test runner script with JUnit XML report generation

## Prerequisites

- Windows Server 2016+ or Windows 10/11
- PowerShell 5.1+ (or PowerShell 7+)
- Pester 5.0+ (auto-installed by Run-Tests.ps1)
- Administrator privileges

## Quick Start

### Run All Tests

```powershell
cd tests/windows
.\Run-Tests.ps1 -ReportPath test-results
```

### Run Specific Test Suite

```powershell
# Run only Firewall tests
.\Run-Tests.ps1 -TestName "Windows Firewall Configuration" -ReportPath test-results

# Run only Security tests
.\Run-Tests.ps1 -TestName "Windows Security Hardening" -ReportPath test-results
```

### View Test Results

```powershell
# Display JUnit XML report
Get-Content test-results/windows_hardening.xml
```

## Test Categories

### 1. Windows Firewall Configuration
- Firewall enabled for all profiles (Domain, Public, Private)
- Default inbound/outbound actions
- SSH rule presence
- OS Typing service port (12345) rule presence

### 2. Windows Security Hardening
- **SMB v1 disabled** — Major security vulnerability
- **Windows Defender** — Real-time protection enabled
- **PowerShell Logging** — Auditing configuration

### 3. Windows System Configuration
- OS identification
- Computer name
- Network adapters
- IPv4 configuration

### 4. Windows Service Configuration
- Critical service status
- Optional services audit

### 5. Windows Hardening Integration
- Overall hardening measures applied
- Basic functionality preserved

## Usage in CI

The tests are automatically run in GitHub Actions CI on Windows runners:

```yaml
# Example CI step
- name: Run Windows Pester tests
  shell: pwsh
  run: |
    cd tests/windows
    .\Run-Tests.ps1 -ReportPath ${{ runner.temp }}/test-results
    
- name: Publish Pester results
  uses: dorny/test-reporter@v1
  if: always()
  with:
    name: windows-hardening
    path: ${{ runner.temp }}/test-results/windows_hardening.xml
    reporter: junit
```

## Helper Functions

### Test-WindowsFirewall
Check Firewall status for all profiles.

```powershell
$Status = Test-WindowsFirewall
$Status | Select-Object Profile, Enabled, DefaultInboundAction
```

### Test-SMBv1Status
Check SMB v1 status.

```powershell
$SMBStatus = Test-SMBv1Status
if ($SMBStatus.Vulnerable) { Write-Warning "SMB v1 is enabled!" }
```

### Test-WindowsDefender
Check Defender configuration.

```powershell
$DefenderStatus = Test-WindowsDefender
$DefenderStatus | Select-Object ServiceRunning, RealtimeMonitoringEnabled
```

### Test-FirewallRule
Check specific firewall rule.

```powershell
$Rule = Test-FirewallRule -RuleName "SSH" -Port 22
if (-not $Rule.RuleExists) { Write-Host "SSH rule missing" }
```

### Get-HardeningStatus
Comprehensive hardening status report.

```powershell
$Status = Get-HardeningStatus
$Status | Format-List
```

### Format-HardeningReport
Pretty-print hardening status.

```powershell
$Status = Get-HardeningStatus
Format-HardeningReport -Status $Status
```

## Customization

Edit **HardeningTests.ps1** to:
- Add/remove test cases
- Change expected firewall rule names
- Adjust service names
- Add organization-specific checks

Edit **helpers.ps1** to:
- Add custom validation functions
- Extend Firewall checks
- Add Defender policies validation

## Troubleshooting

### Pester Not Found
```powershell
Install-Module -Name Pester -Repository PSGallery -Force -Scope CurrentUser
```

### Permission Denied
Run PowerShell as Administrator:
```powershell
Start-Process powershell -Verb RunAs
```

### Tests Skipped
Some tests skip if:
- Running on older Windows versions
- SMB v1 removed from image
- Defender not available (Nano Server, Core)

These are handled gracefully and don't fail the suite.

### WinRM/Remoting Issues
```powershell
# Enable WinRM for remote execution
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
```

## Integration with Ansible

Pester tests validate the hardening applied by Ansible role:

```bash
# Apply Ansible hardening
ansible-playbook -i inventory/hosts.ini site.yml --limit windows

# Run Pester tests to verify
.\tests\windows\Run-Tests.ps1
```

## Best Practices

1. **Run tests after hardening** — Validate deployment
2. **Automate in CI** — Run on every Windows build
3. **Monitor compliance** — Track hardening status over time
4. **Test idempotency** — Run tests multiple times
5. **Document exceptions** — Note any intentional deviations

## References

- [Pester Documentation](https://pester.dev/)
- [PowerShell Scripting](https://learn.microsoft.com/en-us/powershell/)
- [Windows Firewall Cmdlets](https://learn.microsoft.com/en-us/powershell/module/netsecurity/)
- [Windows Defender Protection](https://learn.microsoft.com/en-us/powershell/module/defender/)

## License

Same as os_typing project.
