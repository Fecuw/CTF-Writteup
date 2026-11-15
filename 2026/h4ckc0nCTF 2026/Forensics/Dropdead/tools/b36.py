import sys,string
s=open(sys.argv[1]).read().strip()
A=string.digits+string.ascii_uppercase
print("len",len(s),"alphabet ok:",set(s)<=set(A))
K=2000
pad=(-len(s))%K
t='0'*pad+s
chunks=[int(t[i:i+K],36) for i in range(0,len(t),K)]
BASE=36**K
def conv(c,b):
    if len(c)==1: return c[0],b
    m=len(c)//2
    hi,bh=conv(c[:m],b); lo,bl=conv(c[m:],b)
    return hi*bl+lo, bh*bl
n,_=conv(chunks,BASE)
nb=(n.bit_length()+7)//8
out=n.to_bytes(nb,'big')
open(sys.argv[2],'wb').write(out)
print("decoded bytes:",len(out))
print("first 64 hex:",out[:64].hex())
print("first 200 repr:",repr(out[:200]))
