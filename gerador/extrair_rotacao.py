# Lê o JSON completo do DWG (gerado por: dwgread -O JSON -o mapa.json mapa.dwg)
# e grava rotação/altura de cada texto, usada para traçar as ruas pelos rótulos.
import json,sys
d=json.load(open(sys.argv[1]));out={}
for o in d['OBJECTS']:
    if o.get('entity') in('TEXT','MTEXT'):
        out['%X'%o['handle'][-1]]=[o.get('rotation',0),o.get('height',o.get('text_height',0)),o.get('horiz_alignment',0),o.get('alignment_pt'),o.get('width_factor',1)]
json.dump(out,open(sys.argv[2],'w'));print(len(out),'textos')
