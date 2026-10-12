#!/usr/bin/env python3
"""Unverified LAN compatibility candidate: finite ammo for verified RakNet LAN type 2.
Layers only on the preserved final build; no host/network/security code edits.
"""
import io
from elftools.elf.elffile import ELFFile
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
from patch_fixed_gameplay import GETTERS, getter_code, sha

FINAL_SHA = 'e57f7598839ff65dd6e71e354fd2fc02ab65f414be0a1c23f2aac4a1727c1cce'
MODE_GOT = 0x13bf448
LAN_TYPE = 2


def patch(data):
    if sha(data) != FINAL_SHA:
        raise ValueError('Exact preserved final universal-dual library required')
    elf = ELFFile(io.BytesIO(data))
    ds = elf.get_section_by_name('.dynsym')
    rel = next(r for r in elf.get_section_by_name('.rela.dyn').iter_relocations()
               if r['r_offset'] == MODE_GOT)
    assert rel['r_info_type'] == 1025
    assert ds.get_symbol(rel['r_info_sym']).name == '_currentConnectionType'
    out = bytearray(data)
    changes = []
    for name, va, field, virtual in GETTERS:
        symbol = ds.get_symbol_by_name(name)[0]
        assert (symbol['st_value'], symbol['st_size']) == (va, 204)
        segment = next(s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD'
                       and s['p_vaddr'] <= va and va+204 <= s['p_vaddr']+s['p_filesz'])
        offset = segment['p_offset']+va-segment['p_vaddr']
        old_code, assembly = getter_code(va, field, virtual)
        expected = old_code+bytes.fromhex('1f2003d5')*((204-len(old_code))//4)
        assert data[offset:offset+204] == expected
        # Keep the existing saved this/LR frame; use the existing stock read label.
        guard = f''' adrp x8, {MODE_GOT & ~0xfff}
 ldr x8, [x8, #{MODE_GOT & 0xfff}]
 cbz x8, stock
 ldr w8, [x8]
 cmp w8, #{LAN_TYPE}
 b.eq stock
'''
        assembly = assembly.replace(' mov x19, x0\n', ' mov x19, x0\n'+guard, 1)
        code = bytes(Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN).asm(assembly, addr=va)[0])
        assert len(code) <= 204
        replacement = code+bytes.fromhex('1f2003d5')*((204-len(code))//4)
        out[offset:offset+204] = replacement
        changes.append(dict(function=name, elf_va=hex(va), file_offset=hex(offset),
                            original=expected.hex(), replacement=replacement.hex(),
                            assembly=assembly, code_bytes=len(code)))
    allowed = set()
    for c in changes:
        allowed.update(range(int(c['file_offset'],16), int(c['file_offset'],16)+204))
    assert len(out) == len(data)
    assert all(a == b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
    return bytes(out), dict(input_sha256=sha(data), output_sha256=sha(out), changes=changes,
        policy='ConnectionType 2: original clamped reads, no local refills; other modes retain existing behavior; missing mode pointer fails to finite reads',
        mode_evidence='NetworkManager::useRakNetLAN at 0x7186bc calls setConnectionType(2); GOT relocation identifies _currentConnectionType',
        status='UNVERIFIED LAN candidate; exact runtime triggering field unknown',
        unchanged='Every byte outside the two getter bodies, including fuel, dual policy, firing helper, host validation, networking, security, projectile and reload methods')
