"""CLI integration: contract routing, short witnesses, and rejected premises."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main(out):
    out.mkdir(parents=True,exist_ok=False);source=ROOT/'results/state-witness/guard-contract-v1/private-byte-reader.wasm';rows=[]
    files={'good':{'cells':[[0,66]]},'missing':{'cells':[]},'duplicate':{'cells':[[0,66],[0,66]]},'bad-byte':{'cells':[[0,256]]},'boolean':{'cells':[[0,True]]}}
    for name,data in files.items():(out/(name+'.json')).write_text(json.dumps(data))
    def invoke(name,src,extra,status,code=0):
        dest=out/(name+'-result.json');cmd=[sys.executable,str(HERE/'diagnose.py'),str(src),str(dest)]+extra
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=30);r=json.loads(dest.read_text());assert p.returncode==code and r['status']==status,(name,p.stdout,p.stderr,r)
        rows.append({'name':name,'args':extra,'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'result':r});return r
    for contract in ('full','public','returns'):
        for protocol in ('terminal','reenter'):
            args=['--left','00','--right','10','--observation',contract,'--after-trap',protocol,'--store',str(out/'good.json')]
            negative=contract=='full' or protocol=='reenter';r=invoke(contract+'-'+protocol,source,args,'conditional' if negative else 'unconditional')
            assert r['concreteStoreEvaluation']==('different' if negative else 'equal')
            assert r['method']==('terminal-one-call' if contract=='returns' and protocol=='terminal' else 'relational-fixed-point')
            if negative:assert r['witness']['shortestLength']==(1 if contract=='full' else 2)
    args=['--left','00','--right','10','--observation','public','--after-trap','reenter']
    r=invoke('without-store',source,args,'conditional');assert r['concreteStoreEvaluation']=='not-requested' and r['witness'] is None
    for name in ('missing','duplicate','bad-byte','boolean'):invoke(name,source,args+['--store',str(out/(name+'.json'))],'invalid-input',2)
    boundary=ROOT/'results/state-witness/guard-terminal-boundary-v1/global-phase.wasm'
    invoke('unsupported-global',boundary,['--left','0','--right','1','--observation','returns','--after-trap','terminal'],'unsupported',2)
    invoke('bad-flag-count',source,['--left','0','--right','1','--observation','returns','--after-trap','terminal'],'invalid-input',2)
    (out/'results.json').write_text(json.dumps({'cases':len(rows),'rows':rows,'scope':'CLI selection and premise validation, not an additional semantic theorem.'},indent=2))
    for n in ('diagnose-smoke.py','diagnose.py','guard-terminal-fast.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir()},indent=2));print(json.dumps({'cases':len(rows)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
