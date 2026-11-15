import sys, numpy as np
from PIL import Image
HUES=['R','Y','G','C','B','M']
COLORS={}
light =[(255,192,192),(255,255,192),(192,255,192),(192,255,255),(192,192,255),(255,192,255)]
normal=[(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)]
dark  =[(192,0,0),(192,192,0),(0,192,0),(0,192,192),(0,0,192),(192,0,192)]
for li,row in enumerate([light,normal,dark]):
    for hi,c in enumerate(row): COLORS[c]=(hi,li)
CMDS=[['nop','push','pop'],['add','sub','mul'],['div','mod','not'],
      ['gt','ptr','swi'],['dup','roll','inn'],['inc','outn','outc']]

def run(path, codel=1):
    a=np.array(Image.open(path).convert('RGB'))
    a=a[::codel,::codel,:]
    assert a.shape[0]==1, f"this interpreter handles 1-row programs, got {a.shape}"
    row=[tuple(int(v) for v in px) for px in a[0]]
    runs=[]
    for c in row:
        if runs and runs[-1][0]==c: runs[-1][1]+=1
        else: runs.append([c,1])
    unknown={c for c,_ in runs if c not in COLORS}
    if unknown: print("unknown colours:",unknown,file=sys.stderr)
    stack=[]; out=[]; i=0; dp=0; cc=0; fails=0
    steps=0
    while steps<200000:
        steps+=1
        nxt = i+1 if dp==0 else i-1
        if nxt<0 or nxt>=len(runs):
            fails+=1
            if fails>=8: break
            if fails%2==1: cc^=1
            else: dp=(dp+2)%4 if dp in (0,2) else dp; dp=2 if dp==0 else 0
            continue
        fails=0
        h1,l1=COLORS[runs[i][0]]; h2,l2=COLORS[runs[nxt][0]]
        cmd=CMDS[(h2-h1)%6][(l2-l1)%3]
        sz=runs[i][1]
        try:
            if cmd=='push': stack.append(sz)
            elif cmd=='pop': stack.pop()
            elif cmd=='add': b,a_=stack.pop(),stack.pop(); stack.append(a_+b)
            elif cmd=='sub': b,a_=stack.pop(),stack.pop(); stack.append(a_-b)
            elif cmd=='mul': b,a_=stack.pop(),stack.pop(); stack.append(a_*b)
            elif cmd=='div': b,a_=stack.pop(),stack.pop(); stack.append(a_//b)
            elif cmd=='mod': b,a_=stack.pop(),stack.pop(); stack.append(a_%b)
            elif cmd=='not': stack.append(0 if stack.pop() else 1)
            elif cmd=='gt':  b,a_=stack.pop(),stack.pop(); stack.append(1 if a_>b else 0)
            elif cmd=='ptr': dp=(dp+stack.pop())%4
            elif cmd=='swi': cc=(cc+stack.pop())%2
            elif cmd=='dup': stack.append(stack[-1])
            elif cmd=='roll':
                r=stack.pop(); d=stack.pop()
                if d>0:
                    part=stack[-d:]; del stack[-d:]
                    r%=d; part=part[-r:]+part[:-r]; stack.extend(part)
            elif cmd=='outn': out.append(str(stack.pop()))
            elif cmd=='outc': out.append(chr(stack.pop()%0x110000))
        except (IndexError,ZeroDivisionError,ValueError):
            pass
        i=nxt
    return ''.join(out), stack, steps

if __name__=='__main__':
    o,st,steps=run(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 1)
    print("steps:",steps,"stack tail:",st[-8:])
    print("OUTPUT:",repr(o))
