#!/usr/bin/env python3
"""
@file os_controlsystem_to_junit.py
@brief Convert os_controlsystem output into JUnit XML format for CI reporting.

This script parses os_controlsystem output (granular check results like
[sysctl:key] OK/MISMATCH) and generates JUnit-compatible XML for integration
with CI/CD systems (e.g., GitHub Actions test-reporter).

Usage:
  ./os_controlsystem_to_junit.py --output test-results/os_controlsystem.junit.xml [--input file]
  
If --input is omitted, the script attempts to run ./os_controlsystem --checks all.

@details
Expected input line formats:
  - [sysctl:<key>] OK|MISMATCH expected=.. actual=..
  - [service:exec] OK|MISMATCH ...
  - [service:status] active|inactive
  - [firewall] active and port allowed | port NOT allowed ...
  
Each check is converted to a JUnit testcase; OK results pass, MISMATCH/MISSING fail.
"""
import argparse
import subprocess
import xml.etree.ElementTree as ET
import sys
from datetime import datetime


def parse_output(text):
    # Parse lines into granular checks. Expected line forms:
    #   [sysctl:<key>] OK|MISMATCH expected=.. got=..
    #   [service] active|not active
    #   [service:exec] OK|MISMATCH ...
    #   [firewall] active and port allowed | active but port NOT allowed | ufw not active ...
    results = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # sysctl per-key
        if line.startswith('[sysctl:'):
            end = line.find(']')
            if end != -1:
                key = line[len('[sysctl:'):end]
                ok = True if 'OK' in line else False
                if 'MISMATCH' in line or 'MISSING' in line:
                    ok = False
                results[f'sysctl:{key}'] = {'ok': ok, 'output': line}
                continue
        # generic sysctl check (fallback)
        if line.startswith('[sysctl]'):
            ok = True if 'OK' in line else False
            if 'MISSING' in line:
                ok = False
            results['sysctl'] = {'ok': ok, 'output': line}
            continue
        # service exec check
        if line.startswith('[service:exec]'):
            ok = True if 'OK' in line else False
            if 'MISMATCH' in line:
                ok = False
            results['service:exec'] = {'ok': ok, 'output': line}
            continue
        # service status
        if line.startswith('[service]'):
            ok = True if 'active' in line else False
            if 'not active' in line:
                ok = False
            results['service:status'] = {'ok': ok, 'output': line}
            continue
        # firewall
        if line.startswith('[firewall]'):
            ok = True if 'active and port allowed' in line else False
            if 'NOT allowed' in line or 'not active' in line:
                ok = False
            results['firewall'] = {'ok': ok, 'output': line}
            continue
        # other lines ignored for now

    # If no parsed results, add a fallback entry to indicate parsing happened
    if not results:
        results['parse'] = {'ok': False, 'output': text}
    return results


def make_junit(results, output_path, raw_output):
    testsuite = ET.Element('testsuite')
    testsuite.set('name', 'os_controlsystem')
    testsuite.set('tests', str(len(results)))
    failures = sum(1 for r in results.values() if not r['ok'])
    testsuite.set('failures', str(failures))
    testsuite.set('timestamp', datetime.utcnow().isoformat() + 'Z')

    for name, res in results.items():
        tc = ET.SubElement(testsuite, 'testcase')
        tc.set('classname', 'os_controlsystem')
        # JUnit test names should avoid unescaped special characters; use name as-is
        tc.set('name', name)
        if not res['ok']:
            failure = ET.SubElement(tc, 'failure')
            failure.text = res['output'] or 'Failure (no output)'
        sysout = ET.SubElement(tc, 'system-out')
        sysout.text = res['output']

    # attach raw output as a final testcase
    tc = ET.SubElement(testsuite, 'testcase')
    tc.set('classname', 'os_controlsystem')
    tc.set('name', 'raw-output')
    sout = ET.SubElement(tc, 'system-out')
    sout.text = raw_output

    tree = ET.ElementTree(testsuite)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', help='Input file (if omitted, runs ./os_controlsystem --checks all)')
    p.add_argument('--output', '-o', default='test-results/os_controlsystem.junit.xml', help='Output JUnit XML path')
    args = p.parse_args()

    raw = ''
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            raw = f.read()
    else:
        # try to run the binary
        try:
            proc = subprocess.run(['./os_controlsystem', '--checks', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            raw = proc.stdout.decode('utf-8', errors='replace')
            exit_code = proc.returncode
        except FileNotFoundError:
            print('os_controlsystem binary not found and no --input provided', file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print('Error running os_controlsystem:', e, file=sys.stderr)
            sys.exit(2)

    results = parse_output(raw)
    # ensure output dir exists
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    make_junit(results, args.output, raw)
    # exit with 0 regardless so CI step that runs this script doesn't fail; the test job itself may be non-fatal
    print('Wrote JUnit XML to', args.output)

if __name__ == '__main__':
    main()
