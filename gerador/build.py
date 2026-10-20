import json,re,math,collections,sys
SRC=sys.argv[1]; OUT=sys.argv[2]
d=json.load(open(SRC))
fs=[f for f in d['features'] if f.get('geometry') and f.get('properties')]
OX,OY=723000,8418000
ROT=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
CW=0.85
def tgeom(f,txt):
    x,y=f['geometry']['coordinates'][:2]
    r=ROT.get(f['id'])
    if not r:return x,y,x,y,0.0,3.0
    rot,h,ha,ap,wf=r;h=h or 3.0;wf=wf or 1
    W=len(txt.rstrip())*h*CW*wf;dx,dy=math.cos(rot),math.sin(rot);nx,ny=-dy,dx
    if ha in(1,4) and ap and (ap[0] or ap[1]):x,y=ap[0]-dx*W/2,ap[1]-dy*W/2
    elif ha==2 and ap and (ap[0] or ap[1]):x,y=ap[0]-dx*W,ap[1]-dy*W
    x+=nx*h/2;y+=ny*h/2
    return x,y,x+dx*W,y+dy*W,rot,h
def ok(x,y):return 722000<x<750000 and 8417000<y<8447000
# ---------- lines
def dp(pts,eps):
    if len(pts)<3:return pts
    (x1,y1),(x2,y2)=pts[0],pts[-1];dx,dy=x2-x1,y2-y1;L=math.hypot(dx,dy) or 1e-9
    i,mx=0,-1
    for k in range(1,len(pts)-1):
        x,y=pts[k];dd=abs(dy*x-dx*y+x2*y1-y2*x1)/L
        if dd>mx:mx,i=dd,k
    if mx>eps:return dp(pts[:i+1],eps)[:-1]+dp(pts[i:],eps)
    return [pts[0],pts[-1]]
lines={'q':[],'l':[]}
for f in fs:
    g=f['geometry'];t=g['type']
    rings=[g['coordinates']] if t=='LineString' else (g['coordinates'] if t=='Polygon' else [])
    cls='q' if f['properties'].get('Color')==6 else 'l'
    for r in rings:
        pts=[(p[0],p[1]) for p in r if ok(p[0],p[1])]
        if len(pts)<2:continue
        if len(pts)>3 and math.hypot(pts[0][0]-pts[-1][0],pts[0][1]-pts[-1][1])<0.05:
            k=max(range(len(pts)),key=lambda i:math.hypot(pts[i][0]-pts[0][0],pts[i][1]-pts[0][1]))
            pts=dp(pts[:k+1],0.25)[:-1]+dp(pts[k:],0.25)
        else:pts=dp(pts,0.25)
        q=[(round((x-OX)*10),round((y-OY)*10)) for x,y in pts]
        flat=[q[0][0],q[0][1]]
        for a,b in zip(q,q[1:]):flat+= [b[0]-a[0],b[1]-a[1]]
        lines[cls].append(flat)
# ---------- texts
T=[f for f in fs if f['geometry']['type']=='Point' and 'Text' in f['properties']]
PREF=r'(RU|RUA|AV|AVENIDA|TV|TRAV|PC|PRACA|ESTRADA|EST|VIA|BR|ROD|AL|ALAMEDA|BECO|VIELA|LADEIRA|LOTEAMENTO)'
def clean(s):
    s=s.upper().replace('Ç','C').replace('ª','A')
    s=re.sub(r'JOSE\s*H\.\s*NUNES','JOSE HUMBERTO NUNES',s);s=re.sub(r'\bM(A|ª)\.?\s*FATIMA','MARIA DE FATIMA',s)
    s=re.sub(r'-?\s*LOG\.?\s*[\d\.\s-]*$','',s)
    s=re.sub(r'-?\s*LOG\.?\s*[\d\.]+','',s)
    return re.sub(r'\s+',' ',s).strip(' -/.')
R=[f for f in T if f['properties'].get('Layer')=='TEXTODERUA']
R.sort(key=lambda f:int(f['id'],16))
items=[]
for i,f in enumerate(R):
    raw=f['properties']['Text'];x,y=f['geometry']['coordinates'][:2]
    if not ok(x,y):continue
    ax,ay,bx,by,rot,h=tgeom(f,raw)
    items.append(dict(i=i,raw=raw,t=clean(raw),x=x,y=y,seg=(ax,ay,bx,by),rot=rot,haslog='LOG' in raw.upper()))
for it in items:
    it['start']=bool(re.match(PREF+r'\b|'+PREF+r'\.',it['t']))
starts=[it for it in items if it['start']]
frs=[it for it in items if not it['start']]
for s0 in starts:
    s0['chain']=[s0];s0['closed']=s0['haslog']
used=set()
while True:
    best=None
    for s0 in starts:
        if s0['closed']:continue
        e=s0['chain'][-1]
        for it in frs:
            if id(it) in used or abs(it['i']-s0['i'])>5:continue
            dd=math.hypot(e['x']-it['x'],e['y']-it['y'])
            if dd<200 and (best is None or dd<best[0]):best=(dd,s0,it)
    if not best:break
    _,s0,it=best;used.add(id(it));s0['chain'].append(it)
    if it['haslog']:s0['closed']=True
streets=collections.defaultdict(list)
for s in starts:
    parts=[c['t'] for c in s['chain']]
    name=clean(' '.join(p for p in parts if p))
    name=re.sub(r'\s+',' ',name)
    words=re.sub(PREF+r'\.?','',name).strip()
    if len(re.sub(r'[^A-Z0-9]','',words))<1:continue
    streets[name]+=[c['seg'] for c in s['chain']]
# standalone fragments with descriptive text (not used) -> skip
def pretty(n):
    n=n.title()
    for a,b in [(r'^(Rua|Ru)\b\.?\s*','Rua '),(r'^(Avenida|Av)\b\.?\s*','Av. '),(r'^(Travessa|Trav|Tv)\b\.?\s*','Travessa '),(r'^(Praca|Pc)\b\.?\s*','Praça '),(r'^Est\b\.?\s*','Estrada '),(r'^Br\s*-?\s*(?=\d)','BR-')]:
        n2=re.sub(a,b,n)
        if n2!=n:n=n2;break
    rep=[
         (r'\bBa\.\s*','Bairro '),(r'\bLot\.\s*','Lot. '),(r'\bCond\.\s*','Cond. '),(r'\bDr\.','Dr.'),(r'\bVer\.','Ver.'),(r'\bPres\.','Pres.'),(r'\bCel\.','Cel.'),(r'\bProf\.','Prof.'),(r'\bGbi\b','Guanambi'),(r'\b(De|Da|Do|Dos|Das|E)\b',lambda m:m.group(1).lower())]
    for a,b in rep:n=re.sub(a,b,n)
    n=re.sub(r'\s+',' ',n).strip()
    for a,b in ACC.items():n=re.sub(r'\b'+a+r'\b',b,n)
    n=re.sub(r'^(Rua|Travessa|Av\.|Via Local|Praça) e\b',r'\1 E',n);n=re.sub(r'\bIi\b','II',n);n=re.sub(r'\bIii\b','III',n)
    n=re.sub(r'\s*-\s*',' - ',n);n=re.sub(r'(Lot|Cond)\.(?=\S)',r'\1. ',n)
    return n[0].upper()+n[1:]
ACC={'Jose':'José','Joao':'João','Antonio':'Antônio','Sebastiao':'Sebastião','Sao':'São','Conceicao':'Conceição','Maraba':'Marabá','Brasilia':'Brasília','Getulio':'Getúlio','Vitoria':'Vitória','Pindai':'Pindaí','Ceraima':'Ceraíma','Caicara':'Caiçara','Guimaraes':'Guimarães','Magalhaes':'Magalhães','Goncalves':'Gonçalves','Simoes':'Simões','Lucio':'Lúcio','Julio':'Júlio','Mario':'Mário','Otavio':'Otávio','Flavio':'Flávio','Claudio':'Cláudio','Inacio':'Inácio','Belem':'Belém','Amelia':'Amélia','Galvao':'Galvão','Leao':'Leão','Adao':'Adão','Damiao':'Damião','Estevao':'Estevão','Romao':'Romão','Florencio':'Florêncio','Maria de Fatima':'Maria de Fátima','Fatima':'Fátima','Patrocinio':'Patrocínio','Expedicionarios':'Expedicionários','Petronio':'Petrônio','Barao':'Barão','Uniao':'União','Integracao':'Integração','Esperanca':'Esperança','Assuncao':'Assunção','Ipanema':'Ipanema','Rodoviaria':'Rodoviária','Universitaria':'Universitária','Teofilo':'Teófilo','Helvecio':'Helvécio','Satiro':'Sátiro','Quiteria':'Quitéria','Angelica':'Angélica','Eugenio':'Eugênio','Valerio':'Valério','Euclides':'Euclides','Valdomiro':'Valdomiro','Juscelino':'Juscelino','Clovis':'Clóvis','Moises':'Moisés','Ines':'Inês','Ze':'Zé','Lazaro':'Lázaro','Jesuino':'Jesuíno','Benicio':'Benício','Emilio':'Emílio','Vinicius':'Vinícius','Ataide':'Ataíde','Senhorinha':'Senhorinha','Placido':'Plácido','Isaias':'Isaías','Elias':'Elias','Tomaz':'Tomaz','Libania':'Libânia','Floriano':'Floriano','Gloria':'Glória','Nucleo':'Núcleo','Area':'Área','Cassimiro':'Cassimiro','Parana':'Paraná','Goias':'Goiás','Piaui':'Piauí','Amapa':'Amapá','Ceara':'Ceará','Para':'Pará','Espirito':'Espírito','Mato Grosso':'Mato Grosso'}
def clusters(segs,link=700):
    segs=list(dict.fromkeys(tuple(round(v,1) for v in g) for g in segs))
    n=len(segs);par=list(range(n))
    def fd(a):
        while par[a]!=a:par[a]=par[par[a]];a=par[a]
        return a
    def sd(A,B):return min(math.hypot(A[i]-B[j],A[i+1]-B[j+1]) for i in(0,2) for j in(0,2))
    for a in range(n):
        for b in range(a+1,n):
            if sd(segs[a],segs[b])<link:par[fd(a)]=fd(b)
    g=collections.defaultdict(list)
    for k in range(n):g[fd(k)].append(segs[k])
    return list(g.values())
def geom(segs):
    pts=[];E=[]
    for g in segs:
        i=len(pts);pts+= [(g[0],g[1]),(g[2],g[3])]
        if math.hypot(g[2]-g[0],g[3]-g[1])>0.5:E.append((i,i+1))
    n=len(pts);par=list(range(n))
    def fd(a):
        while par[a]!=a:par[a]=par[par[a]];a=par[a]
        return a
    for a,b in E:par[fd(a)]=fd(b)
    cand=sorted((math.hypot(pts[a][0]-pts[b][0],pts[a][1]-pts[b][1]),a,b) for a in range(n) for b in range(a+1,n))
    for d0,a,b in cand:
        if d0>450:break
        if fd(a)!=fd(b):par[fd(a)]=fd(b);E.append((a,b))
    return pts,E

NUMPTS=[]
for f in T:
    if f['properties'].get('Layer')=='TEXTODERUA':continue
    tx=(f['properties'].get('Text') or '').strip()
    if re.fullmatch(r'\d{1,5}(\s*-?\s*[A-Z])?',tx):
        ax,ay,bx,by,_,_=tgeom(f,tx);NUMPTS.append(((ax+bx)/2,(ay+by)/2))
NB=collections.defaultdict(list)
for p in NUMPTS:NB[(int(p[0]//100),int(p[1]//100))].append(p)
def numsnear(x,y,r):
    out=[]
    for i in range(int((x-r)//100),int((x+r)//100)+1):
        for j in range(int((y-r)//100),int((y+r)//100)+1):out+=NB.get((i,j),[])
    return out
LABMID=[]
def extend(pts,E,name):
    deg=collections.Counter();seg={}
    for a,b in E:deg[a]+=1;deg[b]+=1
    newp=[];newE=[]
    for a,b in E:
        L=math.hypot(pts[b][0]-pts[a][0],pts[b][1]-pts[a][1])
        if L<20:continue
        for p,q in((a,b),(b,a)):
            if deg[q]!=1:continue
            ux,uy=(pts[q][0]-pts[p][0])/L,(pts[q][1]-pts[p][1])/L
            qx,qy=pts[q]
            # other-street labels ahead on the same line block the extension
            stop=1200
            for (mx,my,nm) in LABMID:
                if nm==name:continue
                t=(mx-qx)*ux+(my-qy)*uy
                if 0<t<stop and abs(-(mx-qx)*uy+(my-qy)*ux)<12:stop=t
            ts=sorted(t for (x,y) in numsnear(qx+ux*600,qy+uy*600,700)
                      for t in [(x-qx)*ux+(y-qy)*uy] if 0<t<stop and abs(-(x-qx)*uy+(y-qy)*ux)<16)
            last=0
            for t in ts:
                if t-last>90:break
                last=t
            if last>25:
                newp.append((qx+ux*(last+8),qy+uy*(last+8)));newE.append((q,len(pts)+len(newp)-1))
    return pts+newp,E+newE
out=[]
allc=[]
merged=collections.defaultdict(list)
for name,segs in streets.items():merged[pretty(name)]+=segs
for name,segs in merged.items():
    for g in segs:LABMID.append(((g[0]+g[2])/2,(g[1]+g[3])/2,name))
    for c in clusters(segs):allc.append((name,c))
def cen(c):return sum((g[0]+g[2])/2 for g in c)/len(c),sum((g[1]+g[3])/2 for g in c)/len(c)
# junta "Rua D" sem complemento ao "Rua D - Lot. X" vizinho (mesma rua, rótulo abreviado)
def _md(c1,c2):return min(math.hypot((a[0]+a[2])/2-(b[0]+b[2])/2,(a[1]+a[3])/2-(b[1]+b[3])/2) for a in c1 for b in c2)
_new=[];_bare=[]
for name,c in allc:
    (_bare if re.fullmatch(r'(Rua|Travessa|Av\.|Via Local) [A-Z0-9]{1,2}',name) else _new).append((name,c))
for name,c in _bare:
    cands=[(i,_md(c,c2)) for i,(n2,c2) in enumerate(_new) if n2.startswith(name+' ') and not re.match(r'[A-Za-z0-9]',n2[len(name)+1:len(name)+2] or '#') or n2.startswith(name+' - ') or n2.startswith(name+' Bairro')]
    cands=[z for z in cands if z[1]<600]
    if cands:
        i=min(cands,key=lambda z:z[1])[0];_new[i]=(_new[i][0],_new[i][1]+c)
    else:_new.append((name,c))
allc=_new
cent=[(name,)+cen(c) for name,c in allc]
byname=collections.Counter(n for n,_ in allc)
for idx,(name,c) in enumerate(allc):
    pts,E=geom(c)
    pts,E=extend(pts,E,name)
    cx,cy=cen(c)
    hint=''
    if byname[name]>1 or re.fullmatch(r'(Rua|Travessa|Av\.|Via Local) [A-Z0-9]{1,2}',name):
        near=sorted((math.hypot(x-cx,y-cy),n) for n,x,y in cent if n!=name)
        withb=[z for z in near if z[0]<900 and re.search(r'Bairro|Lot\.|Cond\.',z[1])]
        hint=('perto de '+withb[0][1]) if withb else ('perto de '+near[0][1] if near else '')
    lb=[]
    for g in c:
        ang=math.atan2(g[3]-g[1],g[2]-g[0])
        if ang>math.pi/2:ang-=math.pi
        if ang<-math.pi/2:ang+=math.pi
        lb.append([round(((g[0]+g[2])/2-OX)*10),round(((g[1]+g[3])/2-OY)*10),round(ang,3)])
    out.append(dict(n=name,h=hint,p=[[round((x-OX)*10),round((y-OY)*10)] for x,y in pts],e=[[a,b] for a,b in E],lb=lb))
out.sort(key=lambda s:s['n'])
# ---------- numbers & landmarks
nums=[];marks=[]
SKIP={'TER.','CASA','C A S A','CONST.','TER','C O N S T.'}
for f in T:
    if f['properties'].get('Layer')=='TEXTODERUA':continue
    s=(f['properties'].get('Text') or '').strip()
    if not s:continue
    ax,ay,bx,by,_,_=tgeom(f,s);x,y=(ax+bx)/2,(ay+by)/2
    if not s or not ok(x,y):continue
    X,Y=round((x-OX)*10),round((y-OY)*10)
    if re.fullmatch(r'\d{1,5}(\s*-?\s*[A-Z])?',s) or s=='S/N':nums.append([X,Y,s.replace(' ','')])
    elif s.upper() not in SKIP and len(s)>=4 and re.search(r'[A-Za-z]{3}',s) and not re.fullmatch(r'(AP|APTO|BLOCO|LOTE|QD)\.?\s*\d+',s.upper()):
        marks.append([X,Y,re.sub(r'(?<=\w) (?=\w( |$))','',s) if re.fullmatch(r'(\w )+\w',s) else s])
bairros=set()
for name in streets:
    for m in re.finditer(r'\b(BA|LOT|COND)\.\s*([A-Z0-9 ]{3,30}?)(?=$| -|-|/)',name):
        b=m.group(2).strip()
        if len(b)>=3:bairros.add(pretty(b))
data=dict(o=[OX,OY],q=lines['q'],l=lines['l'],s=out,nm=nums,mk=marks,ba=sorted(bairros))
json.dump(data,open(OUT,'w'),separators=(',',':'),ensure_ascii=False)
print('streets',len(out),'nums',len(nums),'marks',len(marks),'bairros',len(bairros),'q',len(lines['q']),'l',len(lines['l']))
