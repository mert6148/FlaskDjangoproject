const { exec } = require('child_process');

function runCommand(cmd) {
    return new Promise((resolve, reject) => {
        exec(cmd, { windowsHide: true }, (error, stdout, stderr) => {
            if (error) return reject({error, stdout, stderr});
            resolve(stdout.trim());
        });
    });
}

async function main() {
    console.log('Windows JS Koruma Testi basliyor');

    try {
        const firewall = await runCommand('powershell -Command "Get-NetFirewallProfile | Select-Object Name,Enabled | ConvertTo-Json"');
        console.log('Firewall profiler:', JSON.parse(firewall));
    } catch (err) {
        console.error('Firewall testi basarisiz', err.stderr || err.error);
    }

    try {
        const smb = await runCommand('powershell -Command "Get-WindowsOptionalFeature -Online -FeatureName smb1protocol | ConvertTo-Json"');
        console.log('SMB v1 durum:', JSON.parse(smb));
    } catch (err) {
        console.error('SMB testi basarisiz', err.stderr || err.error);
    }

    try {
        const defender = await runCommand('powershell -Command "Get-MpComputerStatus | Select-Object AMServiceEnabled,AntivirusEnabled,RealtimeProtectionEnabled | ConvertTo-Json"');
        console.log('Defender durumu:', JSON.parse(defender));
    } catch (err) {
        console.error('Defender testi basarisiz', err.stderr || err.error);
    }
}

main().catch(console.error);
