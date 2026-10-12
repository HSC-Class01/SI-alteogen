"""DART incremental archival + financial normalization. No secrets in output."""
import argparse, csv, io, json, os, re, time, zipfile
from datetime import date, datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://opendart.fss.or.kr/api/'
CODES = {'11011': 'annual', '11012': 'Half-year', '11013': 'quarterly', '11014': 'quarterly'}
MONTH_CODE = {'12':'11011', '06':'11012', '03':'11013', '09':'11014'}

def read(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    tmp.replace(path)

def number(value):
    if value is None: return None
    s = str(value).strip().replace(',', '').replace(' ', '').replace('−','-')
    if s in ('', '-', '—'): return None
    if s.startswith('(') and s.endswith(')'): s = '-' + s[1:-1]
    try: return int(s)
    except ValueError: return None

def ratio(a, b, positive=False):
    if a is None or b is None or b == 0 or (positive and b <= 0): return None
    return round(100 * a / b, 4)

class Dart:
    def __init__(self, key):
        self.key = key
        self.session = requests.Session()
    def request(self, endpoint, params=None, binary=False):
        params = dict(params or {}, crtfc_key=self.key)
        for attempt in range(5):
            try:
                r = self.session.get(BASE + endpoint, params=params, timeout=(15, 90))
                if r.status_code == 429 or r.status_code >= 500:
                    if attempt < 4: time.sleep(2 ** attempt); continue
                if r.status_code != 200: raise RuntimeError(f'HTTP {r.status_code}: {endpoint}')
                time.sleep(0.15)
                if binary and r.content[:2] == b'PK': return r.content
                if binary:
                    tree = ET.fromstring(r.content)
                    payload = {'status': tree.findtext('status'), 'message': tree.findtext('message')}
                else: payload = r.json()
                status = payload.get('status')
                if status == '000': return payload
                if status in ('013','014'): return None
                if status in ('800','900') and attempt < 4:
                    time.sleep(2 ** attempt); continue
                # Do not log request URL (contains the API key).
                raise RuntimeError(f'DART {status}: {payload.get("message", "API error")} [{endpoint}]')
            except (requests.RequestException, ValueError):
                if attempt == 4: raise RuntimeError(f'Network/parse error: {endpoint}') from None
                time.sleep(2 ** attempt)
        raise RuntimeError(f'Retries exhausted: {endpoint}')
    def corp_code(self):
        blob = self.request('corpCode.xml', binary=True)
        if blob is None: raise RuntimeError('Corporate code archive unavailable')
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            root = ET.fromstring(z.read('CORPCODE.xml'))
        for row in root.findall('list'):
            if row.findtext('stock_code') == '196170': return row.findtext('corp_code')
        raise RuntimeError('Alteogen stock code 196170 not found')
    def reports(self, corp, start):
        results, page = [], 1
        while True:
            p = self.request('list.json', {'corp_code':corp, 'bgn_de':start,
                'end_de':date.today().strftime('%Y%m%d'), 'pblntf_ty':'A',
                'last_reprt_at':'N', 'page_count':100, 'page_no':page, 'sort':'date', 'sort_mth':'asc'})
            if p is None: break
            results += [r for r in p.get('list',[]) if any(t in r['report_nm'] for t in ('사업보고서','반기보고서','분기보고서'))]
            if page >= int(p.get('total_page',1)): break
            page += 1
        return results

def normalize(rows, year, code, basis, metrics):
    result = {'year':year, 'code':code, 'category':CODES[code], 'basis':basis,
              'period':f'{year}-{ {"11011":"FY","11012":"H1","11013":"Q1","11014":"Q3"}[code]}',
              'source':'DART API', 'rcept_no':rows[0].get('rcept_no') if rows else None,
              'values':{}, 'quarter_values':{}, 'provenance':{}, 'issues':[]}
    for key, spec in metrics.items():
        candidates = [r for r in rows if r.get('sj_div') in spec['statements']]
        matched = [r for r in candidates if r.get('account_id') in spec['ids']]
        if not matched:
            matched = [r for r in candidates if re.sub(r'\s+','',r.get('account_nm','')) in spec['names']]
        # Never choose arbitrary first account when multiple conflicting matches exist.
        def val(r):
            if spec['type'] == 'income' and code != '11011':
                cumulative = number(r.get('thstrm_add_amount'))
                return cumulative if cumulative is not None else (number(r.get('thstrm_amount')) if code == '11013' else None)
            return number(r.get('thstrm_amount'))
        distinct = {val(r) for r in matched if val(r) is not None}
        currencies = {r.get('currency') for r in matched if r.get('currency')}
        if currencies and currencies != {'KRW'}:
            distinct = set(); result['issues'].append(f'{key}: non-KRW currency')
        value = next(iter(distinct)) if len(distinct) == 1 else None
        if len(distinct) > 1: result['issues'].append(f'{key}: ambiguous account mapping')
        result['values'][key] = value
        if spec['type'] == 'income':
            qvals = {number(r.get('thstrm_amount')) for r in matched if number(r.get('thstrm_amount')) is not None}
            result['quarter_values'][key] = next(iter(qvals)) if code != '11011' and len(qvals)==1 and (not currencies or currencies=={'KRW'}) else None
        if matched:
            result['provenance'][key] = [{k:r.get(k) for k in ('account_id','account_nm','sj_div','currency','thstrm_amount','thstrm_add_amount','rcept_no')} for r in matched]
    return result

def analyze(records):
    idx = {(r['year'],r['code'],r['basis']):r for r in records}
    for r in records:
        v=r['values']; get=v.get
        prev=idx.get((r['year']-1,r['code'],r['basis']))
        endprev=idx.get((r['year']-1,'11011',r['basis']))
        def avg(k):
            a=get(k); b=endprev['values'].get(k) if endprev else None
            return (a+b)/2 if a is not None and b is not None else None
        r['ratios']={
            'operating_margin':ratio(get('operating_profit'),get('revenue'),True),
            'net_margin':ratio(get('net_income'),get('revenue'),True),
            'debt_ratio':ratio(get('liabilities'),get('equity'),True),
            'current_ratio':ratio(get('current_assets'),get('current_liabilities'),True),
            'equity_ratio':ratio(get('equity'),get('assets'),True),
            'roe_period':ratio(get('net_income'),avg('equity'),True),
            'roa_period':ratio(get('net_income'),avg('assets'),True),
            'revenue_yoy':ratio(get('revenue')-prev['values']['revenue'],prev['values']['revenue'],True)
                if prev and get('revenue') is not None and prev['values'].get('revenue') is not None else None}
        a,b,c=get('assets'),get('liabilities'),get('equity')
        if all(x is not None for x in (a,b,c)) and abs(a-b-c)>max(1000,abs(a)*0.00001):
            r['issues'].append('Balance sheet identity mismatch')
    return records

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--full', action='store_true'); args=parser.parse_args()
    key=os.environ.get('DART_API_KEY','').strip()
    if len(key)!=40: raise SystemExit('DART_API_KEY must be your 40-character Open DART key.')
    api=Dart(key); corp=api.corp_code()
    metrics=read(ROOT/'config/metrics.json',{})
    old=read(ROOT/'data/reports/index.json',[])
    # Re-scan entire receipt history: captures old-year corrections; existing archives are skipped.
    incoming=api.reports(corp,'20100101')
    known={r['rcept_no']:r for r in old}; changes=[]
    for r in incoming:
        path=ROOT/'data/reports'/f'{r["rcept_no"]}.zip'
        if not path.exists():
            blob=api.request('document.xml',{'rcept_no':r['rcept_no']},binary=True)
            if blob is not None:
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    if z.testzip() is not None: raise RuntimeError('Corrupt DART report archive')
                path.write_bytes(blob)
            else: r['archive_status']='not_available'
        if r['rcept_no'] not in known: changes.append(r)
        known[r['rcept_no']]=r
    reports=sorted(known.values(),key=lambda r:r['rcept_no'])
    cache=read(ROOT/'data/financials.json',[])
    records={(r['year'],r['code'],r['basis']):r for r in cache if r.get('source')=='DART API'}
    targets={(y,c) for y in range(max(2015,date.today().year-2),date.today().year+1) for c in CODES}
    if args.full or not cache: targets|={(y,c) for y in range(2015,date.today().year+1) for c in CODES}
    for r in changes:
        match=re.search(r'\((\d{4})\.(\d{2})\)',r['report_nm'])
        if match and int(match[1])>=2015 and match[2] in MONTH_CODE:
            targets.add((int(match[1]),MONTH_CODE[match[2]]))
    for year,code in sorted(targets):
        # Preserve both bases, no silent CFS/OFS fallback or cross-basis ratios.
        for basis in ('CFS','OFS'):
            p=api.request('fnlttSinglAcntAll.json',{'corp_code':corp,'bsns_year':year,'reprt_code':code,'fs_div':basis})
            save(ROOT/'data/raw'/f'{year}_{code}_{basis}.json',p or {'status':'013','message':'No data'})
            if p and p.get('list'):
                records[(year,code,basis)]=normalize(p['list'],year,code,basis,metrics)
    # Legacy figures must be human verified from the archived document, not guessed from table layout.
    manual=ROOT/'data/manual/verified.csv'
    if manual.exists():
        grouped={}
        with manual.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                if not row.get('year'): continue
                y=int(row['year']); c=row['code']; basis=row['basis']; metric=row['metric']
                if not (2010<=y<2015 and c in CODES and basis in ('CFS','OFS') and metric in metrics):
                    raise RuntimeError('Invalid legacy CSV row')
                if not re.fullmatch(r'\d{14}',row.get('rcept_no','')): raise RuntimeError('Legacy row requires source receipt number')
                if row.get('verified','').lower()!='true': continue
                k=(y,c,basis)
                if k not in grouped:
                    grouped[k]={'year':y,'code':c,'basis':basis,'category':CODES[c],
                        'period':f'{y}-{ {"11011":"FY","11012":"H1","11013":"Q1","11014":"Q3"}[c]}',
                        'source':'Verified legacy CSV','rcept_no':row['rcept_no'],'values':{m:None for m in metrics},
                        'quarter_values':{},'provenance':{},'issues':[]}
                if grouped[k]['rcept_no'] != row['rcept_no']: raise RuntimeError('One legacy period must cite one report')
                if metric in grouped[k]['provenance']: raise RuntimeError('Duplicate legacy metric row')
                grouped[k]['values'][metric]=number(row['amount_krw'])
                grouped[k]['provenance'][metric]={'rcept_no':row['rcept_no'],'note':row.get('note',''),'verified':True}
        records.update(grouped)
    final=analyze(sorted(records.values(),key=lambda r:(r['year'],r['code'],r['basis'])))
    save(ROOT/'data/financials.json',final)
    # Publish receipt checkpoint only after normalization succeeds, so failed old-year
    # correction requests are discovered again on the next run.
    save(ROOT/'data/reports/index.json',reports)
    available={(r['year'],r['code'],r['basis']) for r in final}
    coverage=[]
    for y in range(2010,date.today().year+1):
        for c in CODES:
            for basis in ('CFS','OFS'):
                if (y,c,basis) not in available:
                    coverage.append({'year':y,'code':c,'basis':basis,'status':'legacy_manual_required' if y<2015 else 'not_available'})
    save(ROOT/'data/coverage.json',coverage)
    save(ROOT/'data/status.json',{'updated_at':datetime.now(timezone.utc).isoformat(),'corp_code':corp,
        'report_count':len(reports),'new_reports':len(changes),'record_count':len(final),
        'legacy_policy':'2010–2014 original archive + verified manual figures; no fabricated values'})
    print(f'Completed: {len(reports)} report receipts, {len(final)} financial records, {len(changes)} new receipts')

if __name__=='__main__': main()
