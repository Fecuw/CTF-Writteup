#!/usr/bin/env python3
import logging
import time
from pathlib import Path
import angr
import claripy

# ===== 設定 =====
BINARY_PATH = './frankenstein'
BASE_ADDR = 0x00400000
TARGET_ADDR = 0x0040129d
AVOID_ADDRS = [0x00401333]
INPUT_LENGTH = 32
INPUT_MODE = 'stdin'  # stdin / argv
PRINTABLE_ONLY = True
ADD_NEWLINE = True
TIMEOUT = 120

logging.getLogger('angr').setLevel(logging.ERROR)
logging.getLogger('cle').setLevel(logging.ERROR)


def main():
    if not Path(BINARY_PATH).is_file():
        raise FileNotFoundError(BINARY_PATH)
    if BASE_ADDR is None or TARGET_ADDR is None:
        raise ValueError('BASE_ADDR and TARGET_ADDR must be set')
    if INPUT_LENGTH < 1:
        raise ValueError('INPUT_LENGTH must be positive')

    project = angr.Project(BINARY_PATH, auto_load_libs=False)
    loaded_base = project.loader.main_object.mapped_base

    def rebase(addr):
        return loaded_base + addr - BASE_ADDR

    target = rebase(TARGET_ADDR)
    avoid = [rebase(addr) for addr in AVOID_ADDRS]
    print(f'[*] Binary: {BINARY_PATH}')
    print(f'[*] Loaded base: {loaded_base:#x}, Ghidra base: {BASE_ADDR:#x}')
    print(f'[*] Target: {target:#x}, Avoid: {[hex(a) for a in avoid]}')

    chars = [claripy.BVS(f'input_{i}', 8) for i in range(INPUT_LENGTH)]
    symbolic_input = claripy.Concat(*chars)
    if INPUT_MODE == 'stdin':
        data = claripy.Concat(symbolic_input, claripy.BVV(b'\n')) if ADD_NEWLINE else symbolic_input
        state = project.factory.full_init_state(stdin=data)
    elif INPUT_MODE == 'argv':
        # argv must be NUL-terminated; angr handles argument termination.
        state = project.factory.full_init_state(args=[BINARY_PATH, symbolic_input])
        for c in chars:
            state.solver.add(c != 0)
    else:
        raise ValueError('INPUT_MODE must be stdin or argv')

    if PRINTABLE_ONLY:
        for c in chars:
            state.solver.add(c >= 0x20, c <= 0x7e)

    simgr = project.factory.simgr(state)
    simgr.stashes.setdefault("found", [])
    simgr.stashes.setdefault("avoid", [])
    start = time.monotonic()
    print('[*] Exploring...')

    # Step-by-step timeout; does not interrupt a long single solver call.
    while simgr.active and not simgr.found and time.monotonic() - start < TIMEOUT:
        simgr.step()
        simgr.move(from_stash='active', to_stash='found', filter_func=lambda s: s.addr == target)
        if avoid:
            simgr.move(from_stash='active', to_stash='avoid', filter_func=lambda s: s.addr in avoid)

    print(f'[*] Elapsed: {time.monotonic() - start:.2f}s')
    if simgr.found:
        found = simgr.found[0]
        result = found.solver.eval(symbolic_input, cast_to=bytes)
        output = result + (b'\n' if INPUT_MODE == 'stdin' and ADD_NEWLINE else b'')
        Path('solution.bin').write_bytes(output)
        print('[+] TARGET REACHED')
        print('[+] Bytes:', repr(result))
        print('[+] Text :', result.decode('utf-8', errors='replace'))
        print('[+] Hex  :', result.hex())
        print('[+] Saved: solution.bin')
    else:
        print('[-] No solution found')
        if time.monotonic() - start >= TIMEOUT:
            print('[!] Timeout reached (soft limit)')
        print(f'[*] Active={len(simgr.active)}, Avoided={len(simgr.avoid)}, Deadended={len(simgr.deadended)}, Errored={len(simgr.errored)}')
        for error in simgr.errored[:3]:
            print('[!] Error:', error.error)


if __name__ == '__main__':
    main()
