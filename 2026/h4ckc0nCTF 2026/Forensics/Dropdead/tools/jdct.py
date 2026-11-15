import sys, collections

def parse(path):
    d=open(path,'rb').read()
    qt={}; hts={}; sof=None; sos=None; dri=0; i=2
    while i < len(d)-1:
        assert d[i]==0xFF, (i,d[i])
        m=d[i+1]
        if m==0xD8 or 0xD0<=m<=0xD7: i+=2; continue
        ln=int.from_bytes(d[i+2:i+4],'big'); seg=d[i+4:i+2+ln]
        if m==0xDB:
            p=0
            while p<len(seg):
                pq,tq=seg[p]>>4, seg[p]&15; p+=1
                n=64*(2 if pq else 1); qt[tq]=seg[p:p+n]; p+=n
        elif m==0xC4:
            p=0
            while p<len(seg):
                tc,th=seg[p]>>4, seg[p]&15; p+=1
                counts=seg[p:p+16]; p+=16
                total=sum(counts); syms=seg[p:p+total]; p+=total
                # build code->symbol lookup
                code=0; k=0; table={}
                for l in range(1,17):
                    for _ in range(counts[l-1]):
                        table[(l,code)]=syms[k]; k+=1; code+=1
                    code<<=1
                hts[(tc,th)]=table
        elif m==0xC0:
            prec=seg[0]; h=int.from_bytes(seg[1:3],'big'); w=int.from_bytes(seg[3:5],'big')
            nc=seg[5]; comps=[]
            for c in range(nc):
                cid,hv,tq=seg[6+c*3],seg[7+c*3],seg[8+c*3]
                comps.append({'id':cid,'h':hv>>4,'v':hv&15,'tq':tq})
            sof={'w':w,'h':h,'comps':comps}
        elif m in (0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
            print("NOT baseline sequential: SOF marker",hex(m)); sys.exit(1)
        elif m==0xDD:
            dri=int.from_bytes(seg[0:2],'big')
        elif m==0xDA:
            ns=seg[0]; scomps=[]
            for c in range(ns):
                cs,td_ta=seg[1+c*2],seg[2+c*2]
                scomps.append({'id':cs,'dc':td_ta>>4,'ac':td_ta&15})
            sos={'comps':scomps,'data_start':i+2+ln}
            break
        i+=2+ln
    return d,qt,hts,sof,sos,dri

class BR:
    def __init__(s,d,p): s.d=d; s.p=p; s.b=0; s.n=0; s.eof=False
    def bit(s):
        if s.n==0:
            if s.p>=len(s.d): s.eof=True; return 0
            c=s.d[s.p]; s.p+=1
            if c==0xFF:
                nx=s.d[s.p] if s.p<len(s.d) else 0xD9
                if nx==0x00: s.p+=1
                elif 0xD0<=nx<=0xD7: s.p+=1; # shouldn't hit here
                else: s.eof=True; return 0
            s.b=c; s.n=8
        s.n-=1
        return (s.b>>s.n)&1
    def bits(s,k):
        v=0
        for _ in range(k): v=(v<<1)|s.bit()
        return v
    def align(s): s.n=0

def decode_huff(br,table):
    code=0
    for l in range(1,17):
        code=(code<<1)|br.bit()
        if (l,code) in table: return table[(l,code)]
        if br.eof: return None
    return None

def extend(v,t):
    return v - (1<<t) + 1 if t and v < (1<<(t-1)) else v

def run(path):
    d,qt,hts,sof,sos,dri=parse(path)
    comps=sof['comps']
    hmax=max(c['h'] for c in comps); vmax=max(c['v'] for c in comps)
    mcux=-(-sof['w']//(8*hmax)); mcuy=-(-sof['h']//(8*vmax))
    byid={c['id']:c for c in comps}
    for sc in sos['comps']: byid[sc['id']].update(sc)
    print(f"{sof['w']}x{sof['h']}  MCU {mcux}x{mcuy}={mcux*mcuy}  DRI={dri}")
    br=BR(d,sos['data_start'])
    pred={c['id']:0 for c in comps}
    hist={c['id']:collections.Counter() for c in comps}
    dchist={c['id']:collections.Counter() for c in comps}
    nblocks={c['id']:0 for c in comps}
    nz={c['id']:0 for c in comps}; tot={c['id']:0 for c in comps}
    first_ac={c['id']:collections.Counter() for c in comps}
    mcu=0
    try:
        for my in range(mcuy):
            for mx in range(mcux):
                if dri and mcu and mcu%dri==0:
                    br.align()
                    while br.p<len(d)-1 and not (d[br.p]==0xFF and 0xD0<=d[br.p+1]<=0xD7): br.p+=1
                    br.p+=2
                    for k in pred: pred[k]=0
                for c in comps:
                    for by in range(c['v']):
                        for bx in range(c['h']):
                            t=decode_huff(br,hts[(0,c['dc'])])
                            if t is None: raise StopIteration
                            diff=extend(br.bits(t),t) if t else 0
                            pred[c['id']]+=diff
                            dchist[c['id']][max(-64,min(64,pred[c['id']]))]+=1
                            k=1
                            while k<64:
                                rs=decode_huff(br,hts[(1,c['ac'])])
                                if rs is None: raise StopIteration
                                r,s=rs>>4,rs&15
                                if s==0:
                                    if r==15: k+=16; continue
                                    break
                                k+=r
                                if k>63: break
                                v=extend(br.bits(s),s)
                                hist[c['id']][max(-20,min(20,v))]+=1
                                if k<=5: first_ac[c['id']][max(-20,min(20,v))]+=1
                                nz[c['id']]+=1
                                k+=1
                            nblocks[c['id']]+=1
                mcu+=1
                if br.eof: raise StopIteration
    except StopIteration:
        pass
    print(f"decoded MCUs: {mcu}/{mcux*mcuy}  bytes consumed {br.p}/{len(d)}")
    for c in comps:
        cid=c['id']; nb=nblocks[cid]
        print(f"\n--- component {cid} ({'Y' if cid==1 else 'C'})  blocks={nb} ---")
        print(f"  nonzero AC = {nz[cid]}  ({nz[cid]/max(nb,1):.3f} per block, {nz[cid]/max(nb*63,1)*100:.2f}% of AC slots)")
        h=hist[cid]
        print("  AC histogram:")
        for v in range(-6,7):
            print(f"    {v:+3d}: {h[v]:>10d}")
        # chi-square on pairs (2i,2i+1) excluding 0, classic JSteg/OutGuess test
        chi=0.0; dof=0
        for i in range(1,11):
            a,b=h[2*i],h[2*i+1]; n=a+b
            if n>=10:
                e=n/2; chi+=((a-e)**2+(b-e)**2)/e; dof+=1
            a,b=h[-2*i],h[-2*i-1]; n=a+b
            if n>=10:
                e=n/2; chi+=((a-e)**2+(b-e)**2)/e; dof+=1
        print(f"  pair chi-square = {chi:.1f}  dof={dof}   (<< dof  =>  suspicious equalization)")
        r1=h[1]/h[2] if h[2] else 0; rm1=h[-1]/h[-2] if h[-2] else 0
        print(f"  |1|/|2| ratio: +{r1:.3f} / -{rm1:.3f}   (natural JPEG ~2.0-3.5; F5 lowers it)")

run(sys.argv[1])
