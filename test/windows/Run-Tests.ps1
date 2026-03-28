param(
    [string]$TestName = "all",
    [string]$ReportPath = "test-results"
)

<#
    .SYNOPSIS
    Windows hardening Pester test suite for os_typing.
    
    .DESCRIPTION
    Validates Windows OS hardening including:
    - Windows Firewall status and rules
    - SMB v1 disabled
    - Windows Defender enabled
    - Service availability and ports
    
    .PARAMETER TestName
    Specific test to run ("all", "firewall", "security", "services")
    
    .PARAMETER ReportPath
    Output directory for JUnit XML report
    
    .EXAMPLE
    .\Test-WindowsHardening.ps1 -TestName all -ReportPath test-results
#>

param()

# Ensure Pester is installed
$PesterVersion = (Get-Module Pester -ListAvailable | Sort-Object Version -Descending | Select-Object -First 1).Version
if (-not $PesterVersion) {
    Write-Warning "Pester not found. Installing..."
    Install-Module -Name Pester -Repository PSGallery -Force -Scope CurrentUser
}

Import-Module Pester

# Create test result directory
if (-not (Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
}

# Test configuration
$PesterConfig = [PesterConfiguration]::Default
$PesterConfig.Run.Path = $PSScriptRoot
$PesterConfig.Output.Verbosity = "Detailed"
$PesterConfig.TestResult.Enabled = $true
$PesterConfig.TestResult.OutputPath = "$ReportPath\windows_hardening.xml"
$PesterConfig.TestResult.OutputFormat = "JunitXml"
$PesterConfig.CodeCoverage.Enabled = $false

# Run tests
Write-Host "Running Windows hardening Pester tests..." -ForegroundColor Cyan
$Results = Invoke-Pester -Configuration $PesterConfig

# Display summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Green
Write-Host "Passed:  $($Results.PassedCount)" -ForegroundColor Green
Write-Host "Failed:  $($Results.FailedCount)" -ForegroundColor Red
Write-Host "Skipped: $($Results.SkippedCount)" -ForegroundColor Yellow
Write-Host "Report:  $($PesterConfig.TestResult.OutputPath)" -ForegroundColor Cyan

# Exit with appropriate code
exit $Results.FailedCount
