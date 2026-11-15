FRANKENSTEIN'S PASSWORD GENERATOR
SpookyCTF 2026 | Bin/Rev | Medium

Dr. Frankenstein left behind a strange password generator in an abandoned NJIT laboratory. The machine refuses to start without an activation phrase. The doctor's last notebook entry reads, "A bolt at midnight gave it life."

Can you figure out what the program expects and wake the creature?

Your goal is to recover a flag in the format spooky{...}.

Files:
  frankenstein: Linux x86-64 ELF executable

How to run on a Linux x86-64 system:
  chmod +x frankenstein
  ./frankenstein

You can also inspect the file without running it using tools such as strings, objdump, Ghidra, or a hex editor. Use a disposable VM or isolated environment for unfamiliar binaries.

No server or internet connection is required. The executable is provided for Linux x86-64. On Windows or macOS, use a compatible Linux VM or other Linux environment.
