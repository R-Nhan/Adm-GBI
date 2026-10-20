import sys,os
# uso: python3 assemble.py ../site "URL_DO_APPS_SCRIPT" 44.2 43.7
# gera Forms/index.html e Mapa/mapa.html dentro da pasta informada.
# Por compatibilidade, também aceita um arquivo HTML como primeiro argumento e
# grava os dois arquivos na pasta desse arquivo.
# O mapa lê as casas de oração de casas.json (lista de {"comum","nome","lat","lon"}); se o arquivo não existir, não desenha casas.
d=open('data.json').read().replace('<','\\u003c');u=open('utm.js').read().replace("if(typeof module!=='undefined')module.exports=UTM;","")
casas=open('casas.json').read().replace('<','\\u003c') if os.path.exists('casas.json') else '[]'
ep=sys.argv[2] if len(sys.argv)>2 else ''
dx=sys.argv[3] if len(sys.argv)>3 else '0';dy=sys.argv[4] if len(sys.argv)>4 else '0'
def montar(tpl,saida):
    t=open(tpl).read()
    t=t.replace('__DATA__',d).replace('__UTM__',u).replace("'__ENDPOINT__'",repr(ep)).replace('__SATDX__',dx).replace('__SATDY__',dy).replace('__CASAS__',casas)
    open(saida,'w').write(t);print(saida,len(t))
destino=sys.argv[1]
if os.path.splitext(destino)[1].lower() in ('.html','.htm'):
    formulario=destino
    mapa=os.path.join(os.path.dirname(destino) or '.','mapa.html')
else:
    formulario=os.path.join(destino,'Forms','index.html')
    mapa=os.path.join(destino,'Mapa','mapa.html')
    os.makedirs(os.path.dirname(formulario),exist_ok=True)
    os.makedirs(os.path.dirname(mapa),exist_ok=True)
montar('template.html',formulario)
montar('template_mapa.html',mapa)
