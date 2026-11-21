import angr
import claripy

BINARY = "./babyflagchecker"

proj = angr.Project(BINARY, auto_load_libs=False)

# 入力長: 0x27 (39 bytes)
flag = claripy.BVS("flag", 39 * 8)

state = proj.factory.full_init_state(
    args=[BINARY],
    stdin=angr.SimFile(
        name="stdin",
        content=flag,
        has_end=True
    )
)

# ASCII printable characters
for i in range(39):
    c = flag.get_byte(i)
    state.solver.add(c >= 0x20)
    state.solver.add(c <= 0x7e)

simgr = proj.factory.simulation_manager(state)

simgr.explore(
    find=lambda s: b"Correct!" in s.posix.dumps(1),
    avoid=lambda s: b"Wrong..." in s.posix.dumps(1)
)

if simgr.found:
    found = simgr.found[0]
    solution = found.solver.eval(flag, cast_to=bytes)
    print("[+] Found:", solution)
else:
    print("[-] No solution found")
