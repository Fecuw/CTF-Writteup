# One-time offline precomputation of the CSIDH relation lattice (~40 min, PARI).
# Output: relL.sobj  (LLL-reduced basis embedded in solver.py as BASIS)
import time
PR=[3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,179]
p=4*prod(PR)-1
pari.allocatemem(2*2**30, 12*2**30)
t=time.time()
bnf=pari.bnfinit(pari(f"x^2+{p}"))
print("bnf",time.time()-t, bnf.bnf_get_cyc())
cyc=[ZZ(c) for c in bnf.bnf_get_cyc()]
logs=[]
for l in PR:
    for pr in pari.idealprimedec(bnf,l):
        if pari.idealval(bnf,pari("x-1"),pr)>0: break
    logs.append([ZZ(a) for a in pari.bnfisprincipal(bnf,pr,0)])
print("logs",time.time()-t)
n=len(PR); r=len(cyc)
M=matrix(ZZ,n+r,n+r)
W=2**200
for i in range(n):
    M[i,i]=1
    for j in range(r): M[i,n+j]=logs[i][j]*W
for j in range(r): M[n+j,n+j]=cyc[j]*W
B=M.LLL()
rels=[row[:n] for row in B if all(x==0 for x in row[n:])]
print(len(rels), max(v.norm() for v in rels))
save(matrix(ZZ,rels),"relK.sobj")

# ---- restrict from Cl(O_K) (disc -p) to Cl(Z[sqrt(-p)]) (disc -4p), index 3 ----
RK=matrix(ZZ,rels)
D=-4*p
fs=[BinaryQF(l,2,(1+p)//l) for l in PR]; fi=[BinaryQF(l,-2,(1+p)//l) for l in PR]   # ideal (l, sqrt(-p)-1) in Z[sqrt(-p)]
one=BinaryQF(1,0,p)
def ev(v):
    r=one
    for f,g_,e in zip(fs,fi,v):
        for _ in range(abs(int(e))): r=(r*(f if e>0 else g_)).reduced_form()
    return r.reduced_form()
imgs=[ev(v) for v in RK.rows()]
ker=[i for i in imgs if i!=one]
print("nontrivial kernel images:",len(ker))
if ker:
    g=ker[0]; g2=(g*g).reduced_form()
    lab=[0 if i==one else (1 if i==g else 2) for i in imgs]
    assert all(i in (one,g,g2) for i in imgs)
    # sublattice {sum a_j r_j : sum a_j lab_j = 0 mod 3}
    K=matrix(ZZ,[list(r) for r in RK.rows()])
    # kernel of a -> sum a_j lab_j mod 3 in Z^m
    m=len(lab)
    gens=[]
    j0=[j for j in range(m) if lab[j]][0]
    for j in range(m):
        e=vector(ZZ,m)
        if j==j0: e[j]=3
        else: e[j]=1; e[j0]=(-lab[j]*inverse_mod(lab[j0],3))%3
        gens.append(e)
    L=(matrix(ZZ,gens)*K).LLL()
    L=matrix(ZZ,[r for r in L.rows() if r!=0])
else:
    L=RK.LLL()
assert all(ev(r)==one for r in L.rows())
print(L.nrows(), L.det() if L.is_square() else None, max(r.norm(Infinity) for r in L.rows()))
save(L,"relL.sobj")
print([list(r) for r in L.rows()])
