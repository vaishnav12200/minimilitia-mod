#!/usr/bin/env python3
"""Read-only original/final ELF comparison for the L337H4X-WA LAN investigation."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import zipfile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'lan-notification-evidence'
APK = ROOT / 'builds/universal_dual_wield_final/MiniMilitiaClassic-Universal-Dual-v1.0.0.apk'
ORIGINAL_SHA = '2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401'
FINAL_SHA = 'e57f7598839ff65dd6e71e354fd2fc02ab65f414be0a1c23f2aac4a1727c1cce'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    original = (ROOT / 'native-analysis/backup/libcocos2dcpp.so').read_bytes()
    with zipfile.ZipFile(APK) as archive:
        modified = archive.read('lib/arm64-v8a/libcocos2dcpp.so')
    assert sha(original) == ORIGINAL_SHA
    assert sha(modified) == FINAL_SHA
    elf = ELFFile(io.BytesIO(original))
    symbols = elf.get_section_by_name('.dynsym')
    rels = {r['r_offset']: r for r in elf.get_section_by_name('.rela.dyn').iter_relocations()}
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

    def offset(va, size):
        seg = next(s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD'
                   and s['p_vaddr'] <= va and va + size <= s['p_vaddr'] + s['p_filesz'])
        return seg['p_offset'] + va - seg['p_vaddr']

    funcs = [s for s in symbols.iter_symbols() if s['st_info']['type'] == 'STT_FUNC'
             and s['st_size'] and s['st_shndx'] != 'SHN_UNDEF']
    demangled = subprocess.run(['c++filt', *[s.name for s in funcs]], check=True,
                               capture_output=True, text=True).stdout.splitlines()
    records = []
    for symbol, name in zip(funcs, demangled):
        va, size = symbol['st_value'], symbol['st_size']
        off = offset(va, size)
        a, b = original[off:off+size], modified[off:off+size]
        relevant = name.startswith(('ClientRoom::', 'ClientRoomLAN::', 'ServerState::',
                                    'ServerLAN::', 'NetworkManager::', 'NetworkMessageDispatcher::',
                                    'RakNetLocalServer::', 'WeaponStateObject::', 'WeaponManager::'))
        important = name.startswith(('Weapon::getClip(', 'Weapon::getAmmo(', 'Weapon::subAmmo(',
                                     'SoldierLocalController::getPower(',
                                     'SoldierLocalController::addWeapon(',
                                     'SoldierLocalController::fire('))
        if relevant or important:
            records.append({'function': name, 'elf_va': hex(va), 'ghidra_va': hex(va+0x100000),
                            'bytes': size, 'equal': a == b, 'original_sha256': sha(a),
                            'modified_sha256': sha(b)})
    strings = []
    start = 0
    while (pos := original.find(b'L337H4X', start)) >= 0:
        a, b = original.rfind(b'\0', 0, pos)+1, original.find(b'\0', pos)
        assert original[a:b+1] == modified[a:b+1]
        strings.append({'file_offset': hex(a), 'string': original[a:b].decode()})
        start = b+1
    vtables = []
    for cls in ['ClientRoom', 'ClientRoomLAN', 'ServerLAN']:
        vt = symbols.get_symbol_by_name('_ZTV'+str(len(cls))+cls)[0]
        for slot in ([0, 0x60] if cls == 'ServerLAN' else [0xd0, 0x170, 0x180, 0x1b8]):
            r = rels[vt['st_value']+16+slot]
            target = symbols.get_symbol(r['r_info_sym']).name
            name = subprocess.run(['c++filt', target], capture_output=True, text=True, check=True).stdout.strip()
            vtables.append({'class': cls, 'slot': hex(slot), 'target': name})
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / 'binary-comparison.json').write_text(json.dumps({
        'original_native_sha256': sha(original), 'modified_native_sha256': sha(modified),
        'apk_sha256': sha(APK.read_bytes()), 'functions': records, 'strings': strings,
        'vtable_targets': vtables,
        'guard': 'action==2, matching owner/type, then signed STID(+0x64)>SOID(+0x66) OR clip(+0x2a)<0',
        'device_reproduction': 'NOT PERFORMED: no ADB devices connected',
    }, indent=2)+'\n')
    spans = [('drop guard', 0x84309c, 0x843100), ('WA send alert', 0x84387c, 0x843938),
             ('host reduceMagazine', 0x84b164, 0x84b194),
             ('room dispatch message 0x1d', 0x85d658, 0x85d684)]
    lines = []
    for title, a, b in spans:
        off = offset(a, b-a)
        assert original[off:off+b-a] == modified[off:off+b-a]
        lines.append(title + ' (identical original/final; ELF virtual addresses)')
        lines.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                     for i in cs.disasm(original[off:off+b-a], a))
    table = 0x108c46c
    dest = table + struct.unpack_from('<i', original, table+(0x1d-0xf)*4)[0]
    assert dest == 0x85d658
    lines.append(f'room jump table: message 0x1d -> {dest:#x} -> vtable +0x180')
    (OUT / 'original-final-disassembly.txt').write_text('\n'.join(lines)+'\n')
    network = [r for r in records if r['function'].startswith(
        ('ClientRoom::', 'ClientRoomLAN::', 'ServerState::', 'ServerLAN::',
         'NetworkManager::', 'NetworkMessageDispatcher::', 'RakNetLocalServer::', 'WeaponStateObject::'))]
    assert all(r['equal'] for r in network)
    print(f'PASS: {len(network)} room/network/state function bodies unchanged; all {len(strings)} error strings unchanged')
    print('Relevant gameplay differences:')
    for r in records:
        if not r['equal']:
            print(r['function'], r['elf_va'])


if __name__ == '__main__':
    main()
