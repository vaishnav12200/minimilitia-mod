#!/usr/bin/env python3
"""Read-only two-device LAN log capture; never installs, clears logs, or changes settings.
Outputs stay in git-ignored builds/lan_diagnostics/ and may contain private data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.appsomniacs.mmc'


def adb(serial, *args):
    return subprocess.run(['adb', '-s', serial, *args], capture_output=True, text=True,
                          timeout=30)


def snapshot(serial, directory, label):
    commands = {
        'package': ['shell', 'dumpsys', 'package', PACKAGE],
        'apk_paths': ['shell', 'pm', 'path', PACKAGE],
        'abi': ['shell', 'getprop', 'ro.product.cpu.abilist'],
        'android': ['shell', 'getprop', 'ro.build.version.release'],
        'model': ['shell', 'getprop', 'ro.product.model'],
        'mobile_data_setting': ['shell', 'settings', 'get', 'global', 'mobile_data'],
        'airplane_mode_setting': ['shell', 'settings', 'get', 'global', 'airplane_mode_on'],
        'connectivity': ['shell', 'dumpsys', 'connectivity'],
    }
    metadata = {'serial': serial, 'captured_utc': datetime.now(timezone.utc).isoformat()}
    for name, cmd in commands.items():
        result = adb(serial, *cmd)
        (directory / f'{label}-{name}.txt').write_text(result.stdout + result.stderr)
        metadata[name] = {'exit_code': result.returncode}
        if name == 'package':
            metadata['version_lines'] = [line.strip() for line in result.stdout.splitlines()
                                         if 'versionName=' in line or 'versionCode=' in line]
    return metadata


def native_fingerprints(serial):
    """Read installed APKs into temporary files; retain only hashes, never APK copies."""
    result = adb(serial, 'shell', 'pm', 'path', PACKAGE)
    if result.returncode:
        return {'error': result.stderr}
    records = []
    for line in result.stdout.splitlines():
        if not line.startswith('package:'):
            continue
        remote = line[len('package:'):].strip()
        with tempfile.TemporaryDirectory(prefix='mmc-lan-apk-') as temp:
            local = Path(temp) / 'installed.apk'
            pulled = adb(serial, 'pull', remote, str(local))
            if pulled.returncode:
                records.append({'apk': Path(remote).name, 'error': pulled.stderr})
                continue
            with zipfile.ZipFile(local) as archive:
                for name in archive.namelist():
                    if re.fullmatch(r'lib/[^/]+/libcocos2dcpp\.so', name):
                        payload = archive.read(name)
                        records.append({'apk': Path(remote).name, 'entry': name,
                                        'sha256': hashlib.sha256(payload).hexdigest(),
                                        'bytes': len(payload)})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='ADB serial of the hosting phone')
    parser.add_argument('--client', required=True, help='ADB serial of the joining phone')
    parser.add_argument('--seconds', type=int, default=300)
    parser.add_argument('--network-mode', choices=['isolated', 'internet', 'unknown'], default='unknown',
                        help='Operator-reported network condition; this does not change connectivity')
    parser.add_argument('--notes', default='', help='Build names and planned reproduction actions')
    parser.add_argument('--hash-native', action='store_true', help='Pull APKs temporarily to identify native builds')
    args = parser.parse_args()
    if args.host == args.client:
        parser.error('Host and client must be two different devices')
    if not 10 <= args.seconds <= 3600:
        parser.error('--seconds must be between 10 and 3600')
    roles = [('host', args.host), ('client', args.client)]
    pids = {}
    for role, serial in roles:
        state = adb(serial, 'get-state')
        if state.returncode or state.stdout.strip() != 'device':
            parser.error(f'{role} is not an authorized connected ADB device')
        pid = adb(serial, 'shell', 'pidof', PACKAGE).stdout.strip().split()
        if len(pid) != 1 or not pid[0].isdigit():
            parser.error(f'Launch the game on {role} first; expected one main process')
        pids[role] = pid[0]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'builds' / 'lan_diagnostics' / stamp
    output.mkdir(parents=True, exist_ok=False)
    metadata = {'started_utc': datetime.now(timezone.utc).isoformat(),
                'network_mode_operator_reported': args.network_mode, 'notes': args.notes,
                'status': 'capture only; LAN outcome must be recorded manually', 'devices': {}}
    processes, handles = [], []
    try:
        for role, serial in roles:
            directory = output / role
            directory.mkdir()
            out = (directory / 'logcat.txt').open('w')
            err = (directory / 'logcat-errors.txt').open('w')
            handles.extend([out, err])
            processes.append(subprocess.Popen(['adb', '-s', serial, 'logcat', '-b', 'all',
                                              '-v', 'threadtime', '--pid', pids[role]],
                                             stdout=out, stderr=err))
            metadata['devices'][role] = snapshot(serial, directory, 'before')
            metadata['devices'][role]['pid'] = pids[role]
            if args.hash_native:
                metadata['devices'][role]['native_fingerprints'] = native_fingerprints(serial)
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
        print(f'Capturing both game processes for {args.seconds}s: {output}', flush=True)
        print('Reproduce manually; note the popup time and weapon/drop actions. Ctrl-C ends capture.', flush=True)
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            if any(proc.poll() is not None for proc in processes):
                raise RuntimeError('An ADB log stream ended; inspect logcat-errors.txt')
            time.sleep(min(1, max(0, deadline - time.monotonic())))
    except KeyboardInterrupt:
        metadata['stopped_by_operator'] = True
    except Exception as exc:
        metadata['capture_error'] = str(exc)
        raise
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        for handle in handles:
            handle.close()
        metadata['ended_utc'] = datetime.now(timezone.utc).isoformat()
        for role, serial in roles:
            directory = output / role
            if directory.exists():
                try:
                    metadata['devices'].setdefault(role, {})['after'] = snapshot(serial, directory, 'after')
                    metadata['devices'][role]['pid_after'] = adb(serial, 'shell', 'pidof', PACKAGE).stdout.strip()
                except Exception as exc:
                    metadata['devices'].setdefault(role, {})['snapshot_error'] = str(exc)
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('Capture saved. No match result has been inferred; record observations separately.')


if __name__ == '__main__':
    main()
