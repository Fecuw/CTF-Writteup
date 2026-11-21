# babyflagchecker

```C

undefined8 main(void)

{
  int iVar1;
  long in_FS_OFFSET;
  int local_9c;
  byte local_98 [48];
  byte local_68 [48];
  char local_38 [40];
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  printf("flag> ");
  __isoc99_scanf(&DAT_00103017,local_68);
  local_38[0] = '\0';
  local_38[1] = '\0';
  local_38[2] = '\0';
  local_38[3] = '\0';
  local_38[4] = '\0';
  local_38[5] = '\0';
  local_38[6] = '\0';
  local_38[7] = '\0';
  local_38[8] = '\0';
  local_38[9] = '\0';
  local_38[10] = '\0';
  local_38[0xb] = '\0';
  local_38[0xc] = '\0';
  local_38[0xd] = '\0';
  local_38[0xe] = '\0';
  local_38[0xf] = '\0';
  local_38[0x10] = '\0';
  local_38[0x11] = '\0';
  local_38[0x12] = '\0';
  local_38[0x13] = '\0';
  local_38[0x14] = '\0';
  local_38[0x15] = '\0';
  local_38[0x16] = '\0';
  local_38[0x17] = '\0';
  local_38[0x18] = '\0';
  local_38[0x19] = '\0';
  local_38[0x1a] = '\0';
  local_38[0x1b] = '\0';
  local_38[0x1c] = '\0';
  local_38[0x1d] = '\0';
  local_38[0x1e] = '\0';
  local_38[0x1f] = '\0';
  local_38[0x20] = '\0';
  local_38[0x21] = '\0';
  local_38[0x22] = '\0';
  local_38[0x23] = '\0';
  local_38[0x24] = '\0';
  local_38[0x25] = '\0';
  local_38[0x26] = '\0';
  local_38[0x27] = '\0';
  for (local_9c = 0; local_9c < 0x27; local_9c = local_9c + 1) {
    local_38[local_9c] = "ctf{32748901}"[local_9c % 0xd];
    local_38[local_9c + 1] = '\0';
    get_key(local_38,local_9c + 1,local_98);
    local_68[local_9c] = local_68[local_9c] ^ local_98[local_9c % 0x20];
  }
  local_98[0] = 0x25;
  local_98[1] = 0x73;
  local_98[2] = 0x3d;
  local_98[3] = 0xad;
  local_98[4] = 0x56;
  local_98[5] = 0xab;
  local_98[6] = 0x8e;
  local_98[7] = 0x4f;
  local_98[8] = 0xe3;
  local_98[9] = 0x12;
  local_98[10] = 0x1f;
  local_98[0xb] = 0xbd;
  local_98[0xc] = 0xcb;
  local_98[0xd] = 0xe2;
  local_98[0xe] = 0xcf;
  local_98[0xf] = 0x6f;
  local_98[0x10] = 4;
  local_98[0x11] = 0xdd;
  local_98[0x12] = 0x7b;
  local_98[0x13] = 0xa2;
  local_98[0x14] = 0x94;
  local_98[0x15] = 0x5a;
  local_98[0x16] = 0x68;
  local_98[0x17] = 0x2c;
  local_98[0x18] = 0xac;
  local_98[0x19] = 0x3f;
  local_98[0x1a] = 0x95;
  local_98[0x1b] = 0x75;
  local_98[0x1c] = 0x87;
  local_98[0x1d] = 0x16;
  local_98[0x1e] = 0x5b;
  local_98[0x1f] = 0x38;
  local_98[0x20] = 0x50;
  local_98[0x21] = 0xa1;
  local_98[0x22] = 0xe1;
  local_98[0x23] = 8;
  local_98[0x24] = 0xc6;
  local_98[0x25] = 0x81;
  local_98[0x26] = 0x6f;
  iVar1 = strcmp((char *)local_68,(char *)local_98);
  if (iVar1 == 0) {
    puts("Correct!");
  }
  else {
    puts("Wrong...");
  }
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return 0;
}


```

神よ、angrで楽することをお許しください
```bash
╰─ (*'-') < cat solver.py
import angr
import claripy

BINARY = "./babyflagchecker"

proj = angr.Project(BINARY, auto_load_libs=False)

flag = claripy.BVS("flag", 39 * 8)

state = proj.factory.full_init_state(
    args=[BINARY],
    stdin=angr.SimFile(
        name="stdin",
        content=flag,
        has_end=True
    )
)

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

    
╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < python3 solver.py
ERROR    | 2026-11-21 16:29:11,109 | angr.state_plugins.unicorn_engine | failed loading "unicornlib.dylib", unicorn support disabled ('NoneType' object has no attribute 'unicorn_py3')
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | The program is accessing memory with an unspecified value. This could indicate unwanted behavior.
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | 1) setting a value to the initial state
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to suppress these messages.
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | Filling memory at 0x7ffffffeff28 with 8 unconstrained bytes referenced from 0x500028 (strcmp+0x0 in extern-address space (0x28))
WARNING  | 2026-11-21 16:29:44,531 | angr.storage.memory_mixins.default_filler_mixin | Filling memory at 0x7ffffffeff70 with 8 unconstrained bytes referenced from 0x500028 (strcmp+0x0 in extern-address space (0x28))
WARNING  | 2026-11-21 16:29:44,541 | angr.storage.memory_mixins.default_filler_mixin | Filling memory at 0x7ffffffefef7 with 9 unconstrained bytes referenced from 0x500028 (strcmp+0x0 in extern-address space (0x28))
[+] Found: b'TSGLIVE{mondai_tsukuruno_taihendayo...}'
```

# flag
```
TSGLIVE{mondai_tsukuruno_taihendayo...}
```

