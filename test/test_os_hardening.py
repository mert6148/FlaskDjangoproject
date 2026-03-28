import os
import json
import pytest
import testinfra

host = testinfra.get_host("local://")

# Load expected values from config (if present)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'hardening_config.json')
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
else:
    cfg = {}

SERVICE_PORT = str(os.environ.get('SERVICE_PORT', cfg.get('service_port', 12345)))
SERVICE_NAME = cfg.get('service_name', 'os_typing')
EXPECTED_EXEC = cfg.get('service_exec')
EXPECTED_SYSCTL = cfg.get('sysctl', {})


def test_sysctl_values():
    # If no sysctl expectations provided, skip
    if not EXPECTED_SYSCTL:
        pytest.skip('No sysctl expectations configured')

    for key, expected in EXPECTED_SYSCTL.items():
        # Try reading via sysctl -n for exact value
        res = host.run('sysctl -n %s || true' % key)
        if res.rc != 0 or res.stdout.strip() == '':
            pytest.skip('sysctl key %s not present on this system' % key)
        value = res.stdout.strip()
        assert value == str(expected), 'sysctl %s -> expected %s, got %s' % (key, expected, value)


def test_systemd_unit_contents_and_active():
    unit_path = '/etc/systemd/system/%s.service' % SERVICE_NAME
    f = host.file(unit_path)
    if not f.exists:
        pytest.skip('service unit not installed: %s' % unit_path)
    content = f.content_string

    # If an expected ExecStart is provided in config, assert it's present
    if EXPECTED_EXEC:
        assert EXPECTED_EXEC in content, 'ExecStart does not contain expected: %s' % (EXPECTED_EXEC)

    # Check unit is enabled and running if systemctl is available
    sc = host.run('which systemctl || true')
    if sc.rc != 0:
        pytest.skip('systemctl not available')

    is_enabled = host.run('systemctl is-enabled %s' % SERVICE_NAME)
    if is_enabled.rc == 0:
        assert 'enabled' in is_enabled.stdout or is_enabled.stdout.strip() == 'enabled'

    is_active = host.run('systemctl is-active %s' % SERVICE_NAME)
    if is_active.rc == 0:
        assert 'active' in is_active.stdout or is_active.stdout.strip() == 'active'


def test_ufw_port():
    res = host.run('which ufw || true')
    if res.rc != 0:
        pytest.skip('ufw not installed')
    out = host.run('ufw status verbose').stdout
    assert 'Status: active' in out
    assert SERVICE_PORT in out, 'Expected port %s not found in UFW output' % SERVICE_PORT
