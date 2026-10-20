# Uso: python3 localizar_casas.py data.json enderecos.json
# enderecos.json = [["comum", "nome da rua (sem 'Rua')", "número"], ...]
# Mostra, para cada endereço, a posição achada na planta (exato / entre números / vizinho) e a distância ao rótulo
# 'Congregação Cristã' mais próximo da planta. Copie lat/lon para casas.json.
import json, math, re, sys, unicodedata
# Localiza endereços na planta (mesma lógica do formulário) e devolve lat/lon SIRGAS2000.
D = json.load(open(sys.argv[1]))
OX, OY = D['o']; SAT = (44.2, 43.7)

def norm(s):
    s = unicodedata.normalize('NFD', s); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', s.lower())).strip()
DROP = set('rua r av avenida travessa tv praca pc estrada bairro ba lot loteamento cond de da do dos das e'.split())
def toks(s): return [t for t in norm(s).split() if t and t not in DROP]

ST = [{'n': s['n'], 'h': s.get('h', ''), 'pts': [(p[0]/10, p[1]/10) for p in s['p']], 'e': s['e'], 'tk': toks(s['n'])} for s in D['s']]
NUMS = [(a[0]/10, a[1]/10, str(a[2])) for a in D['nm']]

def segd(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
    t = max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L)) if L else 0
    return math.hypot(px-ax-t*dx, py-ay-t*dy)
def dstreet(s, x, y):
    d = min(math.hypot(p[0]-x, p[1]-y) for p in s['pts'])
    for a, b in s['e']:
        A, B = s['pts'][a], s['pts'][b]; d = min(d, segd(x, y, A[0], A[1], B[0], B[1]))
    return d
def parseN(t):
    m = re.match(r'^0*(\d+)-?([A-Z]?)$', re.sub(r'\s', '', str(t).upper())); return (int(m[1]), m[2]) if m else None

def inv(E, N):  # SIRGAS 2000 / UTM 23S -> lat, lon (mesmas fórmulas de utm.js)
    a=6378137; f=1/298.257222101; k0=0.9996; e2=f*(2-f); ep2=e2/(1-e2); L0=math.radians(-45)
    x=E-500000; y=N-10000000; M=y/k0; mu=M/(a*(1-e2/4-3*e2*e2/64-5*e2**3/256)); e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    p1=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1*e1/16-55*e1**4/32)*math.sin(4*mu)+(151*e1**3/96)*math.sin(6*mu)+(1097*e1**4/512)*math.sin(8*mu)
    s=math.sin(p1); c=math.cos(p1); t=math.tan(p1); C1=ep2*c*c; T1=t*t; N1=a/math.sqrt(1-e2*s*s); R1=a*(1-e2)/(1-e2*s*s)**1.5; Dd=x/(N1*k0)
    lat=p1-(N1*t/R1)*(Dd*Dd/2-(5+3*T1+10*C1-4*C1*C1-9*ep2)*Dd**4/24+(61+90*T1+298*C1+45*T1*T1-252*ep2-3*C1*C1)*Dd**6/720)
    lon=L0+(Dd-(1+2*T1+C1)*Dd**3/6+(5-2*C1+28*T1-3*C1*C1+8*ep2+24*T1*T1)*Dd**5/120)/c
    return math.degrees(lat), math.degrees(lon)

def localizar(rua, num):
    q = toks(rua); alvo = parseN(num)
    cands = [s for s in ST if all(any(k == t or k.startswith(t) for k in s['tk']) for t in q)]
    exatas = [s for s in cands if s['tk'] == q] or cands
    res = []
    for s in exatas:
        perto = [(n, dstreet(s, n[0], n[1])) for n in NUMS
                 if min(math.hypot(p[0]-n[0], p[1]-n[1]) for p in s['pts']) < 900]
        perto = [(n, d) for n, d in perto if d < 45]
        hit = [(n, d) for n, d in perto if parseN(n[2]) and parseN(n[2])[0] == alvo[0]]
        if hit:
            n, d = min(hit, key=lambda h: h[1]); res.append(('exato', s, n[0], n[1], f'número {n[2]} a {d:.0f} m da rua')); continue
        lo = hi = None
        for n, d in perto:
            p = parseN(n[2])
            if not p or d > 28: continue
            if p[0] < alvo[0] and (not lo or p[0] > lo[0]): lo = (p[0], n)
            if p[0] > alvo[0] and (not hi or p[0] < hi[0]): hi = (p[0], n)
        if lo and hi and math.hypot(lo[1][0]-hi[1][0], lo[1][1]-hi[1][1]) < 250:
            k = (alvo[0]-lo[0])/(hi[0]-lo[0])
            res.append(('aprox', s, lo[1][0]+(hi[1][0]-lo[1][0])*k, lo[1][1]+(hi[1][1]-lo[1][1])*k, f'entre {lo[0]} e {hi[0]}')); continue
        r = lo or hi
        if r: res.append(('vizinho', s, r[1][0], r[1][1], f'mais próximo: {r[0]}'))
        else: res.append(('so-rua', s, None, None, 'nenhum número perto'))
    return cands, res

CCB = [(a[0]/10, a[1]/10) for a in D['mk'] if re.search(r'CONGREGACAO|CRISTA', a[2])]
for comum, rua, num in json.load(open(sys.argv[2])):
    cands, res = localizar(rua, num)
    print(f'\n== {comum}: {rua}, {num}  ({len(cands)} trecho(s) com nome compatível)')
    for k, s, x, y, info in res:
        if x is None: print(f'   [{k}] {s["n"]} ({s["h"]}) — {info}'); continue
        lat, lon = inv(x+OX-SAT[0], y+OY-SAT[1])
        dccb = min(math.hypot(x-c[0], y-c[1]) for c in CCB)
        print(f'   [{k}] {s["n"]} ({s["h"]}) — {info} -> {lat:.6f}, {lon:.6f}  | rótulo CCB da planta a {dccb:.0f} m')
