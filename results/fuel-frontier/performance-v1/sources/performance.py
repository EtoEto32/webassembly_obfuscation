import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import transform as t

HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('performance.py','performance.cjs','performance-plan.md','transform.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    # Source artifacts are immutable; stage the extra optimized original here.
    staging=out/'inputs';staging.mkdir();shutil.copy2(source/'manifest.json',staging/'manifest.json')
    mf=json.loads((source/'manifest.json').read_text())
    for f in mf['fixtures']:
        dest=staging/f['name'];dest.mkdir()
        for p in (source/f['name']).glob('*-O3.wasm'):shutil.copy2(p,dest/p.name)
        t.w.tool('wasm-opt',[source/f['name']/'original.wasm','-O3','-o',dest/'original-O3.wasm'])
        t.w.tool('wasm-validate',[dest/'original-O3.wasm'])
    order=[(mode,i) for mode in ('original','dynamic','late','whole','segment','frontier','manual') for i in range(4)]
    random.Random(2026102406).shuffle(order);results=[]
    try:
        for mode,rep in order:
            cmd=['node','--expose-gc',str(HERE/'performance.cjs'),str(staging),mode]
            r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            (out/(mode+'-'+str(rep)+'.log.json')).write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
            if r.returncode:raise RuntimeError(r.stderr)
            row=json.loads(r.stdout);row['rep']=rep;results.append(row)
            (out/'raw.json').write_text(json.dumps(results,indent=2),encoding='utf8')
        summary=[]
        for f in mf['fixtures']:
            name=f['name'];subset={mode:[r for proc in results if proc['mode']==mode for r in proc['rows'] if r['name']==name] for mode in ('original','dynamic','late','whole','segment','frontier','manual')}
            assert len({r['checksum'] for rows in subset.values() for r in rows})==1
            for mode,rows in subset.items():
                values=[r['medianNs'] for r in rows];q=statistics.quantiles(values,n=4,method='inclusive')
                summary.append({'name':name,'mode':mode,'medianNs':statistics.median(values),'q1Ns':q[0],'q3Ns':q[2],'bytes':rows[0]['bytes'],'charges':rows[0]['lastCharges']})
        report={'source':str(source),'seed':2026102406,'order':order,'summary':summary}
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        lines=['# fuel frontier 性能実測','','各値は4 fresh processのprocess中央値から計算。単位ns/call。IQRは別JSON。CPU時間保証ではない。','', '|例|original|whole|segment|frontier|manual|dynamic|late|','|---|---:|---:|---:|---:|---:|---:|---:|']
        for f in mf['fixtures']:
            vals={r['mode']:r['medianNs'] for r in summary if r['name']==f['name']}
            lines.append('|'+f['name']+'|'+'|'.join('%.1f'%vals[m] for m in ('original','whole','segment','frontier','manual','dynamic','late'))+'|')
        (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
        print('\n'.join(lines))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
