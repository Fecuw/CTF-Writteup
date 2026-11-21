import sys, numpy as np
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
sys.path.insert(0, sys.argv[1])
from decipher import DeCipher, SBOX, RCON
par=lambda x: bin(x).count('1')&1
V=[0]+[a for a in range(1,256) if len({SBOX[x]^SBOX[x^a] for x in range(256)})==1]
assert len(V)==64
ms=[m for m in range(1,256) if all(par(m&v)==0 for v in V)]
m1,m2=ms[0],[m for m in ms if m!=ms[0]][0]
pi=lambda x:(par(m1&x),par(m2&x))
e1=[x for x in range(256) if pi(x)==(1,0)][0]; e2=[x for x in range(256) if pi(x)==(0,1)][0]
def wof(p1,p2): return (e1 if p1 else 0)^(e2 if p2 else 0)
c=lambda v: SBOX[v]^SBOX[0]
Ccol=[]
for i in range(8):
    x=1<<i; p=pi(x); Ccol.append(c(x^wof(*p)))
def Cl(x):
    r=0
    for i in range(8):
        if x>>i&1: r^=Ccol[i]
    return r
T={(a,b):SBOX[wof(a,b)] for a in (0,1) for b in (0,1)}
assert all(SBOX[x]==Cl(x)^T[pi(x)] for x in range(256))
print("decomposition ok", flush=True)

NV=128+40*3; CONST=1<<NV
def byteconst(v): return [CONST if v>>i&1 else 0 for i in range(8)]
def bxor(a,b): return [x^y for x,y in zip(a,b)]
def Cexpr(xb):
    out=[0]*8
    for i in range(8):
        for j in range(8):
            if Ccol[i]>>j&1: out[j]^=xb[i]
    return out
def piexpr(xb, m): 
    r=0
    for i in range(8):
        if m>>i&1: r^=xb[i]
    return r
def xtime(b): # b bits list
    hi=b[7]; out=[0]+b[:7]
    for i in range(8):
        if 0x1b>>i&1: out[i]^=hi
    return out
def gmul(b,k):
    r=[0]*8; cur=b
    while k:
        if k&1: r=bxor(r,cur)
        cur=xtime(cur); k>>=1
    return r
def mix(st):
    st=list(st)
    for i in range(4):
        col=i*4; v0,v1,v2,v3=st[col:col+4]
        st[col]=bxor(bxor(bxor(gmul(v0,2),v3),v2),gmul(v1,3))
        st[col+1]=bxor(bxor(bxor(gmul(v1,2),v0),v3),gmul(v2,3))
        st[col+2]=bxor(bxor(bxor(gmul(v2,2),v1),v0),gmul(v3,3))
        st[col+3]=bxor(bxor(bxor(gmul(v3,2),v2),v1),gmul(v0,3))
    return st
def shift(b):
    b=list(b)
    b[1],b[5],b[9],b[13]=b[5],b[9],b[13],b[1]
    b[2],b[6],b[10],b[14]=b[10],b[14],b[2],b[6]
    b[3],b[7],b[11],b[15]=b[15],b[3],b[7],b[11]
    return b
def lin_inv(d):
    s=bytearray(bytes(d)); DeCipher.mix_columns_inv(s); DeCipher.shift_rows_inv(s); return s

def solve(P,Cc,pr):
    eqs=[]
    # key schedule symbolic
    k0=[[1<<(8*b+i) for i in range(8)] for b in range(16)]
    words=[k0[4*i:4*i+4] for i in range(4)]
    nxt=[128]
    def sbox_sym(xb):
        v=nxt[0]; nxt[0]+=3
        p1,p2,q=1<<v,1<<(v+1),1<<(v+2)
        eqs.append(piexpr(xb,m1)^p1); eqs.append(piexpr(xb,m2)^p2)
        t0=T[(0,0)]; d1=T[(1,0)]^t0; d2=T[(0,1)]^t0; d3=T[(0,0)]^T[(1,0)]^T[(0,1)]^T[(1,1)]
        out=Cexpr(xb)
        for i in range(8):
            if t0>>i&1: out[i]^=CONST
            if d1>>i&1: out[i]^=p1
            if d2>>i&1: out[i]^=p2
            if d3>>i&1: out[i]^=q
        return out
    for i in range(4,44):
        temp=list(words[i-1])
        if i%4==0:
            temp=temp[1:]+temp[:1]
            temp=[sbox_sym(x) for x in temp]
            temp[0]=bxor(temp[0],byteconst(RCON[i//4-1]))
        words.append([bxor(a,b) for a,b in zip(words[i-4],temp)])
    rks=[sum(words[4*r:4*r+4],[]) for r in range(11)]
    # pi knowledge for encryption 0 state^rk at each round
    pis=[]
    for r in range(10):
        row=[]
        Ds={j:lin_inv(pr[0,j,r+1]) for j in range(1,16)}
        for b in range(16):
            cs=[u for u in range(256) if all(SBOX[u^pr[0,j,r,b]]^SBOX[u]==Ds[j][b] for j in range(1,16))]
            ps={pi(u) for u in cs}; assert len(ps)==1,(r,b,len(cs)); row.append(cs[0])
        pis.append(row)
    for n in range(16):
        st=[byteconst(int(x)) for x in P[n]]
        for r in range(10):
            new=[]
            for b in range(16):
                y=bxor(st[b],rks[r][b])
                u=pis[r][b]^int(pr[0,n,r,b])
                p=pi(u)
                eqs.append(piexpr(y,m1)^(CONST if p[0] else 0))
                eqs.append(piexpr(y,m2)^(CONST if p[1] else 0))
                o=Cexpr(y)
                o=bxor(o,byteconst(T[p]))
                new.append(o)
            st=mix(shift(new))
        out=[bxor(st[b],rks[10][b]) for b in range(16)]
        for b in range(16):
            for i in range(8):
                eqs.append(out[b][i]^(CONST if int(Cc[n][b])>>i&1 else 0))
    # gaussian elimination
    piv={}
    for e in eqs:
        for pv,row in piv.items():
            if e>>pv&1: e^=row
        e&= (1<<(NV+1))-1
        if e==0: continue
        if e==CONST: raise Exception("inconsistent")
        lead=(e&(CONST-1)).bit_length()-1
        for pv in list(piv):
            if piv[pv]>>lead&1: piv[pv]^=e
        piv[lead]=e
    print("rank",len(piv),"of",NV, flush=True)
    key=bytearray(16)
    for i in range(128):
        assert i in piv, f"free var {i}"
        row=piv[i]; assert (row&(CONST-1))==(1<<i)
        if row&CONST: key[i//8]|=1<<(i%8)
    return bytes(key)

for stage in (1,2):
    d=np.load(f"{sys.argv[1]}/output_stage{stage}.npz")
    key=solve(d['plaintexts'],d['ciphertexts'],d['proofs'])
    c=DeCipher(key)
    assert all(c.encrypt(bytes(d['plaintexts'][i]))==bytes(d['ciphertexts'][i]) for i in range(16))
    print("stage",stage,"key",key.hex(), flush=True)
    if stage==1: aes=AESGCM(c.decrypt(bytes(d['wrapped_key'])))
    else: aes=AESGCM(sha256(c._round_keys).digest())
    print(aes.decrypt(b'\0'*12,bytes(d['flag']),None).decode(), flush=True)
