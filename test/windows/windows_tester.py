#!/usr/bin/env python
"""Windows sistem koruma testi araçı (Python)."""
import json
import platform
import subprocess


def check_firewall():
    # PowerShell komutu ile devlet duvarı durumu sorgulandı.
    cmd = ["powershell", "-Command", "Get-NetFirewallProfile | Select-Object Name,Enabled | ConvertTo-Json"]
    output = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT)
    return json.loads(output)


def check_smb_v1():
    cmd = ["powershell", "-Command", "Get-WindowsOptionalFeature -Online -FeatureName smb1protocol | ConvertTo-Json"]
    output = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT)
    data = json.loads(output)
    enabled = data.get("State", "Unknown") == "Enabled"
    return {"FeatureName": "smb1protocol", "Enabled": enabled, "State": data.get("State")}


def check_defender():
    cmd = ["powershell", "-Command", "Get-MpComputerStatus | Select-Object AMServiceEnabled,AMServiceVersion,AntispywareEnabled,AntivirusEnabled,RealTimeProtectionEnabled | ConvertTo-Json"]
    output = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT)
    return json.loads(output)


def main():
    print("Windows Koruma Testi: Basliyor")
    print("Sistem:", platform.platform())

    try:
        firewall = check_firewall()
        print("Firewall profiler:\n", json.dumps(firewall, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as exc:
        print("Firewall testi basarisiz:", exc.output)

    try:
        smb = check_smb_v1()
        print("SMB v1 durum:", smb)
    except subprocess.CalledProcessError as exc:
        print("SMB testi basarisiz:", exc.output)

    try:
        defender = check_defender()
        print("Defender durumu:\n", json.dumps(defender, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as exc:
        print("Defender testi basarisiz:", exc.output)


if __name__ == "__main__":
    main()
