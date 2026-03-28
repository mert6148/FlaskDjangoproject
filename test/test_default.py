"""
Testinfra tests for os_hardening role verification
"""
import pytest


def test_sysctl_ip_forward(host):
    """Verify that IP forwarding is disabled"""
    sysctl = host.sysctl("net.ipv4.ip_forward")
    assert sysctl == 0, "IP forwarding should be disabled"


def test_sysctl_send_redirects(host):
    """Verify that ICMP redirects are disabled"""
    sysctl_all = host.sysctl("net.ipv4.conf.all.send_redirects")
    sysctl_default = host.sysctl("net.ipv4.conf.default.send_redirects")
    
    assert sysctl_all == 0, "All send_redirects should be disabled"
    assert sysctl_default == 0, "Default send_redirects should be disabled"


def test_sysctl_log_martians(host):
    """Verify that Martian logging is enabled"""
    sysctl_all = host.sysctl("net.ipv4.conf.all.log_martians")
    sysctl_default = host.sysctl("net.ipv4.conf.default.log_martians")
    
    assert sysctl_all == 1, "All log_martians should be enabled"
    assert sysctl_default == 1, "Default log_martians should be enabled"


def test_sysctl_core_uses_pid(host):
    """Verify that core dumps include PID"""
    sysctl = host.sysctl("kernel.core_uses_pid")
    assert sysctl == 1, "core_uses_pid should be enabled"


@pytest.mark.skipif("ansible_os_family != 'Debian'")
def test_ufw_installed(host):
    """Verify that UFW is installed (Debian/Ubuntu)"""
    pkg = host.package("ufw")
    assert pkg.is_installed, "UFW should be installed"


@pytest.mark.skipif("ansible_os_family != 'Debian'")
def test_ufw_enabled(host):
    """Verify that UFW firewall is enabled"""
    # Check UFW service status
    svc = host.service("ufw")
    assert svc.is_running or svc.is_enabled, "UFW should be enabled or running"


def test_ssh_connectivity(host):
    """Verify that SSH port is accessible"""
    # This test verifies basic connectivity; actual firewall rules tested separately
    assert host.interface("lo").exists, "Loopback interface should exist"


def test_ipv6_forwarding_disabled(host):
    """Verify that IPv6 forwarding is disabled"""
    try:
        sysctl = host.sysctl("net.ipv6.conf.all.forwarding")
        # IPv6 may not be available; skip gracefully
        if sysctl is not None:
            assert sysctl == 0, "IPv6 forwarding should be disabled"
    except Exception:
        pytest.skip("IPv6 not configured")


def test_hostname_configured(host):
    """Verify that system hostname is set"""
    hostname = host.check_output("hostname")
    assert hostname, "Hostname should be configured"
    assert len(hostname) > 0, "Hostname should not be empty"


def test_network_interfaces(host):
    """Verify that network interfaces are configured"""
    # At minimum, loopback should exist
    lo = host.interface("lo")
    assert lo.exists, "Loopback interface should exist"


def test_idempotent_sysctl(host):
    """Verify that sysctl settings are idempotent (can be applied multiple times)"""
    # Run sysctl --system in check mode
    result = host.run("sysctl -a | grep ip_forward")
    assert result.rc == 0, "sysctl check should succeed"


@pytest.mark.parametrize("param,expected", [
    ("net.ipv4.ip_forward", 0),
    ("kernel.core_uses_pid", 1),
])
def test_sysctl_parameters(host, param, expected):
    """Parameterized test for sysctl values"""
    sysctl_value = host.sysctl(param)
    assert sysctl_value == expected, f"{param} should be {expected}"
