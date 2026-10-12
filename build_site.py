import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
    data={name:json.loads((ROOT/f'data/{name}.json').read_text(encoding='utf-8')) for name in ('financials','status','coverage')}
    data['metrics']=json.loads((ROOT/'config/metrics.json').read_text(encoding='utf-8'))
    data['peers']=json.loads((ROOT/'config/peers.json').read_text(encoding='utf-8'))
    data['reports']=json.loads((ROOT/'data/reports/index.json').read_text(encoding='utf-8'))
    template=(ROOT/'site/template.html').read_text(encoding='utf-8')
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\u003c')
    # Escaping HTML-sensitive literal characters prevents an embedded closing script tag.
    payload=payload.replace(chr(60),chr(92)+'u003c')
    (ROOT/'site/index.html').write_text(template.replace('__DATA__',payload),encoding='utf-8')
    print('Built site/index.html:',len(data['financials']),'financial records')
if __name__=='__main__': build()
