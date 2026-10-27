import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import prototype as p
from fixtures import fixtures

HERE=Path(__file__).resolve().parent


def scalar(program, selected, profile, x, y):
    """Independent concrete evaluator; no Z3 expression evaluation."""
    local=[x&p.U32,y&p.U32]+[0]*len(program.locals)
    def value(e):
        name=e[0]
        if name=='i32.const':return int(e[1],0)&p.U32
        if name=='local.get':return local[int(e[1])]
        if name=='i8x16.extract_lane_u':
            sw=e[2];a=value(sw[1][1])&255;index=value(sw[2][1])&255
            strict=sw[0]==p.STRICT or program.ids[id(sw)] in selected or profile==0
            return a if index<16 or (index<128 and not strict) else 0
        if name=='i32.eqz':return int(value(e[1])==0)
        if name=='select':
            a,b,c=map(value,e[1:]);return a if c else b
        a,b=map(value,e[1:])
        if name=='i32.and':return a&b
        if name=='i32.or':return a|b
        if name=='i32.xor':return a^b
        if name=='i32.add':return (a+b)&p.U32
        if name=='i32.sub':return (a-b)&p.U32
        if name=='i32.mul':return (a*b)&p.U32
        if name=='i32.shl':return (a<<(b&31))&p.U32
        if name=='i32.shr_u':return a>>(b&31)
        if name=='i32.eq':return int(a==b)
        if name=='i32.ne':return int(a!=b)
        if name=='i32.lt_u':return int(a<b)
        raise ValueError(name)
    for e in program.body[:-1]:local[int(e[1])]=value(e[2])
    return value(program.body[-1])


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('plan.md','prototype.py','fixtures.py','probe.py','run.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(p.ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-reader.py')
    rng=random.Random(2026102421);edges=[0,1,15,16,17,31,32,63,64,127,128,129,255,256,65535,0x7fffffff,0x80000000,0xffffffff]
    inputs=list(itertools.product(edges,repeat=2))+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(512)]
    rows=[];request={'directory':str(out),'inputs':inputs,'rows':[]};checked=0
    try:
        for fixture in fixtures():
            name=fixture['name'];source=out/(name+'-source.wasm');p.compile_mod(fixture['module'],source);program=p.read(source);n=len(program.sites)
            aware=p.synthesize(program,fixture['weights']);independent=p.synthesize(program,fixture['weights'],True)
            _,dependencies=program.model([False]*n,[p.z.BoolVal(False)]*n)
            modes={'original':[],'all':list(range(n)),'slice':sorted(dependencies),'independent':independent['selected'],'aware':aware['selected']}
            enumerated=[]
            if n<=6:
                for mask in range(1<<n):
                    selected=[i for i in range(n) if mask>>i&1];witness=p.query(program,selected)
                    enumerated.append({'selected':selected,'stable':witness is None,'witness':witness})
                costs=[sum(aware['weights'][i] for i in r['selected']) for r in enumerated if r['stable']]
                assert min(costs)==aware['cost']
            files=[];expected={};emulated={};measurements={}
            for mode,selected in modes.items():
                target=out/(name+'-'+mode+'.wasm');begin=time.perf_counter();p.compile_mod(p.rewritten(program,selected),target)
                measurements[mode]={'bytes':target.stat().st_size,'rewriteValidateMs':(time.perf_counter()-begin)*1000,'selected':selected}
                files.append(target.name);expected[target.name]=[scalar(program,selected,0,x,y) for x,y in inputs]
                for profile in (0,1):
                    target=out/(name+'-'+mode+'-profile'+str(profile)+'.wasm');p.compile_mod(p.rewritten(program,selected,profile),target)
                    files.append(target.name);emulated[target.name]=[scalar(program,selected,profile,x,y) for x,y in inputs]
            request['rows'].append({'name':name,'files':files})
            rows.append({'name':name,'sites':n,'aware':aware,'independent':independent,'measurements':measurements,'enumerated':enumerated,'expected':expected,'emulated':emulated})
            print(name+': '+str(len(aware['selected']))+'/'+str(n)+' sites',flush=True)
        (out/'request.json').write_text(json.dumps(request),encoding='utf8')
        command=['node',str(HERE/'run.cjs'),str(out/'request.json')];run=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (out/'node.log').write_text(run.stderr,encoding='utf8');(out/'node.json').write_text(run.stdout,encoding='utf8')
        if run.returncode:raise RuntimeError(run.stderr)
        actual=json.loads(run.stdout)
        for row,observed in zip(rows,actual['rows']):
            for file,values in observed['results'].items():
                if file in row['emulated']:assert values==row['emulated'][file],file
                elif '-original.' not in file:assert values==row['expected'][file],file
                else:
                    allowed0=row['emulated'][file.replace('.wasm','-profile0.wasm')];allowed1=row['emulated'][file.replace('.wasm','-profile1.wasm')]
                    assert values==allowed0 or values==allowed1,file
                checked+=len(values)
            del row['expected'];del row['emulated']
        (out/'results.json').write_text(json.dumps({'seed':2026102421,'inputs':len(inputs),'valueChecks':checked,'rows':rows,'node':{k:v for k,v in actual.items() if k!='rows'},'limitations':'Generated straight-line splat subset, one native engine plus explicit profile models. Symbolic queries concern the model, not a verified parser/compiler/engine.'},indent=2),encoding='utf8')
        print(json.dumps({'fixtures':len(rows),'valueChecks':checked}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
