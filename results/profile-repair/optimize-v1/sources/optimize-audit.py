"""Audit ordinary optimization and independently reread repaired binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import prototype as p

HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('optimize-audit.py','prototype.py','run.cjs'):shutil.copy2(HERE/name,out/'sources'/name)
    request=json.loads((source/'request.json').read_text());request['directory']=str(out);rows=[];newrows=[]
    old=json.loads((source/'node.json').read_text());reference={r['name']:r['results'] for r in old['rows']};checks=0
    try:
        for row in request['rows']:
            name=row['name'];files=[];record={'name':name,'modes':{}}
            for mode in ('original','all','slice','independent','aware'):
                file=name+'-'+mode+'.wasm';target=out/(name+'-'+mode+'-O3.wasm')
                shutil.copy2(source/file,out/file)
                start=time.perf_counter();p.w.tool('wasm-opt',[out/file,'-O3','--enable-simd','--enable-relaxed-simd','-o',target]);elapsed=(time.perf_counter()-start)*1000
                p.w.tool('wasm-validate',[target]);text=p.w.tool('wasm2wat',[target,'--fold-exprs']);target.with_suffix('.wat').write_text(text,encoding='utf8')
                counts={code:sum(e[0]==code for e in p.walk(p.w.parse(text))) for code in (p.RELAXED,p.STRICT)}
                facts={'bytes':target.stat().st_size,'optimizeValidateMs':elapsed,'instructionCounts':counts}
                for version,path in (('raw',out/file),('O3',target)):
                    try:program=p.read(path)
                    except ValueError as error:facts[version+'Symbolic']={'status':'unsupported','reason':str(error)}
                    else:
                        witness=p.query(program,[]);facts[version+'Symbolic']={'status':'unsat' if witness is None else 'sat','witness':witness}
                        if mode!='original':assert witness is None,(name,mode,version)
                record['modes'][mode]=facts;files.append(target.name)
            rows.append(record);newrows.append({'name':name,'files':files})
        request['rows']=newrows;(out/'request.json').write_text(json.dumps(request),encoding='utf8')
        run=subprocess.run(['node',str(HERE/'run.cjs'),str(out/'request.json')],capture_output=True,text=True,timeout=60)
        (out/'node.json').write_text(run.stdout,encoding='utf8');(out/'node.log').write_text(run.stderr,encoding='utf8')
        if run.returncode:raise RuntimeError(run.stderr)
        actual=json.loads(run.stdout)
        for row in actual['rows']:
            for file,values in row['results'].items():
                prior=file.replace('-O3.wasm','.wasm')
                if '-original.' in prior:
                    allowed=[reference[row['name']][prior.replace('.wasm','-profile'+str(i)+'.wasm')] for i in (0,1)]
                    assert values in allowed,file
                else:assert values==reference[row['name']][prior],file
                checks+=len(values)
        (out/'results.json').write_text(json.dumps({'rows':rows,'valueChecks':checks,'limitations':'Symbolic verifier shares evaluator with synthesis; rereading catches rewrite mistakes but is not an independent formal proof. Unsupported optimized shapes are reported separately.'},indent=2),encoding='utf8')
        print(json.dumps({'fixtures':len(rows),'valueChecks':checks,'unsupported':sum(v.get(k,{}).get('status')=='unsupported' for r in rows for v in r['modes'].values() for k in ('rawSymbolic','O3Symbolic'))}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();main(args.source.resolve(),args.output.resolve())
