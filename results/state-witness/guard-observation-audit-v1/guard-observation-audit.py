"""Separate original API observations from instrumentation-only store witnesses."""
import argparse,collections,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def return_contract(model,left,right,has_read):
    if has_read:return {'status':'unsupported-read-api','reason':'outcome-only projection would erase a byte-reading API'}
    queue=collections.deque([(tuple(left),tuple(right),[])]);seen={(tuple(left),tuple(right))};transitions=0
    while queue:
        left,right,word=queue.popleft()
        if left==right:continue
        for a in model['actions']:
            if a['readonly']:continue # only constant returns remain after has_read check
            l,r=g.effect(model,left,a),g.effect(model,right,a);transitions+=1
            if l['outcome']!=r['outcome']:return {'status':'distinguishable','word':word+[a['name']],'states':len(seen),'transitions':transitions}
            pair=(l['alive'],r['alive'])
            if pair not in seen:seen.add(pair);queue.append((*pair,word+[a['name']]))
    return {'status':'equivalent-under-return-trap-contract','states':len(seen),'transitions':transitions}
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);original=json.loads((source/'manifest.json').read_text());rows=[]
    for row in original['rows']:
        module=k.p.read(source/row['source']);model=g.parse(module);public=[];has_read=False;funcs=k.p.section(module,'func')
        for e in k.p.section(module,'export'):
            kind,index=e[2][0],int(e[2][1])
            if kind in ('memory','table'):public.append({'resource':0 if kind=='memory' else index+1,'name':json.loads(e[1]),'kind':kind})
            if kind=='func':has_read|=any(isinstance(x,list) and x and x[0]=='i32.load8_u' for x in funcs[index])
        rows.append({**row,'publicResources':public,'hasMemoryReadApi':has_read,'returnTrapContract':return_contract(model,row['left'],row['right'],has_read)})
    manifest={'source':str(source.resolve()),'sourceEvidenceSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),'rows':rows}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for n in ('guard-observation-audit.py','guard-observation-audit.mjs','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    p=subprocess.run(['node',str(out/'guard-observation-audit.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));assert p.returncode==0,p.stderr;print(p.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
