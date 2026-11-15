#!/usr/bin/env python3
import angr
import claripy
import logging
import time

# ============================================================
# CONFIGURATION - ここだけ変更
# ============================================================

import angr
import claripy
import logging
import time

# ============================================================
# CONFIGURATION - ここだけ変更
# ============================================================

BINARY_PATH = "./frankenstein"       # 例: "./chall"

BASE_ADDR = 0x00400000        # GhidraのImage Base (例: 0x400000)
TARGET_ADDR = 0x0040129d     # 到達したいアドレス (例: 0x401234)

AVOID_ADDRS = [0x00401333]       # 回避したいアドレス (例: [0x401200])

INPUT_LENGTH = 32      # 探索する入力バイト数
INPUT_MODE = "stdin"   # "stdin" または "argv"

PRINTABLE_ONLY = True  # True: ASCII 0x20〜0x7e
ADD_NEWLINE = True     # stdinの末尾に改行を付ける

TIMEOUT = 120          # 探索時間上限（秒）

# ============================================================
# LOGGING
# ============================================================

logging.getLogger("angr").setLevel(logging.ERROR)
logging.getLogger("cle").setLevel(logging.ERROR)

def main():
    if not BINARY_PATH:
              raise ValueError("BINARY_PATH を設定してください")

                  if BASE_ADDR is None:
                            raise ValueError("BASE_ADDR を設定してください")

                                if TARGET_ADDR is None:
                                          raise ValueError("TARGET_ADDR を設定してください")

                                              if INPUT_LENGTH <= 0:
                                                        raise ValueError("INPUT_LENGTH must be positive")

                                                            print("[*] Loading binary:", BINARY_PATH)

                                                                project = angr.Project(
                                                                        BINARY_PATH,
                                                                                auto_load_libs=False
                                                                                    )

                                                                    loaded_base = project.loader.main_object.mapped_base

                                                                        print(f"[*] Loaded base : {loaded_base:#x}")
                                                                            print(f"[*] Ghidra base : {BASE_ADDR:#x}")

                                                                                # Ghidraの仮想アドレスをangrのアドレスへ変換
                                                                                    def rebase(addr):
                                                                                            return loaded_base + (addr - BASE_ADDR)

                                                                                                target = rebase(TARGET_ADDR)
                                                                                                    avoid = [rebase(addr) for addr in AVOID_ADDRS]

                                                                                                        print(f"[*] Target      : {target:#x}")
                                                                                                            print(f"[*] Avoid       : {[hex(x) for x in avoid]}")

                                                                                                                # --------------------------------------------------------
                                                                                                                    # Symbolic input
                                                                                                                        # --------------------------------------------------------

                                                                                                                            chars = [
                                                                                                                                    claripy.BVS(f"input_{i}", 8)
                                                                                                                                            for i in range(INPUT_LENGTH)
                                                                                                                                                  ]

                                                                                                                                                      symbolic_input = claripy.Concat(*chars)

                                                                                                                                                          if INPUT_MODE == "stdin":
                                                                                                                                                                    stdin_data = (
                                                                                                                                                                                claripy.Concat(symbolic_input, claripy.BVV(b"\n"))
                                                                                                                                                                                            if ADD_NEWLINE
                                                                                                                                                                                                          else symbolic_input
                                                                                                                                                                                                                    )

                                                                                                                                                                            state = project.factory.full_init_state(
                                                                                                                                                                                        stdin=stdin_data
                                                                                                                                                                                                )

                                                                                                                                                                                elif INPUT_MODE == "argv":
                                                                                                                                                                                        state = project.factory.full_init_state(
                                                                                                                                                                                                    args=[BINARY_PATH, symbolic_input]
                                                                                                                                                                                                            )

                                                                                                                                                                                            else:
                                                                                                                                                                                                      raise ValueError("INPUT_MODE must be stdin or argv")

                                                                                                                                                                                                          # --------------------------------------------------------
                                                                                                                                                                                                              # Constraints
                                                                                                                                                                                                                  # --------------------------------------------------------

                                                                                                                                                                                                                      if PRINTABLE_ONLY:
                                                                                                                                                                                                                                for c in chars:
                                                                                                                                                                                                                                              state.solver.add(c >= 0x20)
                                                                                                                                                                                                                                                          state.solver.add(c <= 0x7e)

                                                                                                                                                                                                                                                              # --------------------------------------------------------
                                                                                                                                                                                                                                                                  # Symbolic execution
                                                                                                                                                                                                                                                                      # --------------------------------------------------------

                                                                                                                                                                                                                                                                          simgr = project.factory.simgr(state)

                                                                                                                                                                                                                                                                              start = time.monotonic()
                                                                                                                                                                                                                                                                                  timed_out = False

                                                                                                                                                                                                                                                                                      print("[*] Starting symbolic execution...")

                                                                                                                                                                                                                                                                                          def stop_on_timeout(_):
                                                                                                                                                                                                                                                                                                  nonlocal timed_out
                                                                                                                                                                                                                                                                                                          if time.monotonic() - start >= TIMEOUT:
                                                                                                                                                                                                                                                                                                                        timed_out = True
                                                                                                                                                                                                                                                                                                                                    return True
                                                                                                                                                                                                                                                                                                                                            return False

                                                                                                                                                                                                                                                                                                                                                simgr.explore(
                                                                                                                                                                                                                                                                                                                                                        find=target,
                                                                                                                                                                                                                                                                                                                                                                avoid=avoid,
                                                                                                                                                                                                                                                                                                                                                                        step_func=lambda sm: (
                                                                                                                                                                                                                                                                                                                                                                                    sm.stash(
                                                                                                                                                                                                                                                                                                                                                                                                    filter_func=lambda s: stop_on_timeout(s),
                                                                                                                                                                                                                                                                                                                                                                                                                    from_stash="active",
                                                                                                                                                                                                                                                                                                                                                                                                                                    to_stash="timeout"
                                                                                                                                                                                                                                                                                                                                                                                                                                                )
                                                                                                                                                                                                                                                                                                                                                                                                if not timed_out
                                                                                                                                                                                                                                                                                                                                                                                                              else sm
                                                                                                                                                                                                                                                                                                                                                                                                                        )
                                                                                                                                                                                                                                                                                                                                                                            )

                                                                                                                                                                                                                                                                                                                                                    # --------------------------------------------------------
                                                                                                                                                                                                                                                                                                                                                        # Results
                                                                                                                                                                                                                                                                                                                                                            # --------------------------------------------------------

                                                                                                                                                                                                                                                                                                                                                                elapsed = time.monotonic() - start

                                                                                                                                                                                                                                                                                                                                                                    print(f"[*] Elapsed: {elapsed:.2f}s")

                                                                                                                                                                                                                                                                                                                                                                        if simgr.found:
                                                                                                                                                                                                                                                                                                                                                                                  found = simgr.found[0]

                                                                                                                                                                                                                                                                                                                                                                                          result = found.solver.eval(
                                                                                                                                                                                                                                                                                                                                                                                                      symbolic_input,
                                                                                                                                                                                                                                                                                                                                                                                                                  cast_to=bytes
                                                                                                                                                                                                                                                                                                                                                                                                                          )

                                                                                                                                                                                                                                                                                                                                                                                                  print("\n" + "=" * 60)
                                                                                                                                                                                                                                                                                                                                                                                                          print("[+] TARGET REACHED")
                                                                                                                                                                                                                                                                                                                                                                                                                  print("=" * 60)

                                                                                                                                                                                                                                                                                                                                                                                                                          print("[+] Bytes :", repr(result))
                                                                                                                                                                                                                                                                                                                                                                                                                                  print("[+] String:", result.decode("utf-8", errors="replace"))
                                                                                                                                                                                                                                                                                                                                                                                                                                          print("[+] Hex   :", result.hex())

                                                                                                                                                                                                                                                                                                                                                                                                                                                  with open("solution.bin", "wb") as f:
                                                                                                                                                                                                                                                                                                                                                                                                                                                              f.write(result)

                                                                                                                                                                                                                                                                                                                                                                                                                                                                          if INPUT_MODE == "stdin" and ADD_NEWLINE:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            f.write(b"\n")

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    print("[+] Saved : solution.bin")

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  print("[-] No solution found")

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          if timed_out:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        print("[!] Timeout reached")

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                print("[*] Active :", len(simgr.active))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        print("[*] Avoided:", len(simgr.avoid))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                print("[*] Deadended:", len(simgr.deadended))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        print("[*] Errored:", len(simgr.errored))

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                for err in simgr.errored[:3]:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              print("[!] Error:", err.error)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              if __name__ == "__main__":
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    main()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    # 例: "./chall"

BASE_ADDR = None       # GhidraのImage Base (例: 0x400000)
TARGET_ADDR = None     # 到達したいアドレス (例: 0x401234)

AVOID_ADDRS = []       # 回避したいアドレス (例: [0x401200])

INPUT_LENGTH = 32      # 探索する入力バイト数
INPUT_MODE = "stdin"   # "stdin" または "argv"

PRINTABLE_ONLY = True  # True: ASCII 0x20〜0x7e
ADD_NEWLINE = True     # stdinの末尾に改行を付ける

TIMEOUT = 120          # 探索時間上限（秒）

# ============================================================
# LOGGING
# ============================================================

logging.getLogger("angr").setLevel(logging.ERROR)
logging.getLogger("cle").setLevel(logging.ERROR)

def main():
    if not BINARY_PATH:
        raise ValueError("BINARY_PATH を設定してください")

    if BASE_ADDR is None:
        raise ValueError("BASE_ADDR を設定してください")

    if TARGET_ADDR is None:
        raise ValueError("TARGET_ADDR を設定してください")

    if INPUT_LENGTH <= 0:
        raise ValueError("INPUT_LENGTH must be positive")

    print("[*] Loading binary:", BINARY_PATH)

    project = angr.Project(
        BINARY_PATH,
        auto_load_libs=False
    )

    loaded_base = project.loader.main_object.mapped_base

    print(f"[*] Loaded base : {loaded_base:#x}")
    print(f"[*] Ghidra base : {BASE_ADDR:#x}")

    # Ghidraの仮想アドレスをangrのアドレスへ変換
    def rebase(addr):
        return loaded_base + (addr - BASE_ADDR)

    target = rebase(TARGET_ADDR)
    avoid = [rebase(addr) for addr in AVOID_ADDRS]

    print(f"[*] Target      : {target:#x}")
    print(f"[*] Avoid       : {[hex(x) for x in avoid]}")

    # --------------------------------------------------------
    # Symbolic input
    # --------------------------------------------------------

    chars = [
        claripy.BVS(f"input_{i}", 8)
        for i in range(INPUT_LENGTH)
    ]

    symbolic_input = claripy.Concat(*chars)

    if INPUT_MODE == "stdin":
        stdin_data = (
            claripy.Concat(symbolic_input, claripy.BVV(b"\n"))
            if ADD_NEWLINE
            else symbolic_input
        )

        state = project.factory.full_init_state(
            stdin=stdin_data
        )

    elif INPUT_MODE == "argv":
        state = project.factory.full_init_state(
            args=[BINARY_PATH, symbolic_input]
        )

    else:
        raise ValueError("INPUT_MODE must be stdin or argv")

    # --------------------------------------------------------
    # Constraints
    # --------------------------------------------------------

    if PRINTABLE_ONLY:
        for c in chars:
            state.solver.add(c >= 0x20)
            state.solver.add(c <= 0x7e)

    # --------------------------------------------------------
    # Symbolic execution
    # --------------------------------------------------------

    simgr = project.factory.simgr(state)

    start = time.monotonic()
    timed_out = False

    print("[*] Starting symbolic execution...")

    def stop_on_timeout(_):
        nonlocal timed_out
        if time.monotonic() - start >= TIMEOUT:
            timed_out = True
            return True
        return False

    simgr.explore(
        find=target,
        avoid=avoid,
        step_func=lambda sm: (
            sm.stash(
                filter_func=lambda s: stop_on_timeout(s),
                from_stash="active",
                to_stash="timeout"
            )
            if not timed_out
            else sm
        )
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    elapsed = time.monotonic() - start

    print(f"[*] Elapsed: {elapsed:.2f}s")

    if simgr.found:
        found = simgr.found[0]

        result = found.solver.eval(
            symbolic_input,
            cast_to=bytes
        )

        print("\n" + "=" * 60)
        print("[+] TARGET REACHED")
        print("=" * 60)

        print("[+] Bytes :", repr(result))
        print("[+] String:", result.decode("utf-8", errors="replace"))
        print("[+] Hex   :", result.hex())

        with open("solution.bin", "wb") as f:
            f.write(result)

            if INPUT_MODE == "stdin" and ADD_NEWLINE:
                f.write(b"\n")

        print("[+] Saved : solution.bin")

    else:
        print("[-] No solution found")

        if timed_out:
            print("[!] Timeout reached")

        print("[*] Active :", len(simgr.active))
        print("[*] Avoided:", len(simgr.avoid))
        print("[*] Deadended:", len(simgr.deadended))
        print("[*] Errored:", len(simgr.errored))

        for err in simgr.errored[:3]:
            print("[!] Error:", err.error)


if __name__ == "__main__":
    main()

