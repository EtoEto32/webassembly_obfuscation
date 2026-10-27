"""Boundary, second-engine and constraint-rank audits, kept separate from main run."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import transform as T
from attack import recover


def main(run,out):
    out.mkdir(parents=True,exist_ok=False);m=json.loads((run/'manifest.json').read_text())
    checked=[]
    for row in m['rows']:
        data=(run/row['wasm']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        if row['optimization']!='O3':continue
        truth=bytes.fromhex(m['truth'][row['fixture']]);s=row['shift']
        for x in [0,(row['n']>>s)-1,65534>>s,(65534>>s)+1,0x80000000,0xffffffff]:
            stdout=T.W.tool('wasm-interp',[run/row['wasm'],'-r','run','-a','i32:'+str(x)]).strip()
            a=(x<<s)&0xffffffff;expected='memory_oob' if a+1>=65536 else str((truth[a] if a<len(truth) else 0)^(truth[a+1] if a+1<len(truth) else 0))
            match=re.search(r'=> i32:(\d+)$',stdout)
            actual=match.group(1) if match else ('memory_oob' if 'out of bounds' in stdout else stdout)
            checked.append({'wasm':row['wasm'],'input':x,'stdout':stdout,'expected':expected,'actual':actual,'equal':actual==expected})
    assert all(r['equal'] for r in checked)
    rank_tests=[]
    for n,s,offsets in itertools.product([3,6,8],[0,1,2],[(0,1),(1,3),(0,0)]):
        groups={};count=max(0,(n-min(offsets)+(1<<s)-1)//(1<<s))
        for data in itertools.product([0,1],repeat=n):
            answer=tuple((data[i*(1<<s)+offsets[0]] if i*(1<<s)+offsets[0]<n else 0)^
                         (data[i*(1<<s)+offsets[1]] if i*(1<<s)+offsets[1]<n else 0) for i in range(count))
            groups.setdefault(answer,[]).append(data)
        for answer,preimages in groups.items():
            result=recover(answer,n,s,offsets)
            assert len(preimages)==1<<result['free_components']
            assert tuple(result['representative']) in preimages
        rank_tests.append({'n':n,'shift':s,'offsets':offsets,'images':len(groups),'preimages':1<<n})
    try:recover([1],1,0,(0,0))
    except ValueError:contradiction_rejected=True
    else:raise AssertionError('Contradiction accepted')
    boundary=[]
    for s,offsets in itertools.product([0,1,8,15],[(0,1),(1,7),(65535,0),(65535,65535)]):
        label=f's{s}-o{offsets[0]}-{offsets[1]}'
        module=T.source_module(bytes(range(32)),s,offsets)
        module.insert(3,['data',['i32.const','65528'],'"\\01\\02\\03\\04\\05\\06\\07\\08"'])
        module.insert(4,['data',['i32.const','65535'],'"\\a5"'])
        src=out/(label+'-original.wasm');dst=out/(label+'-projected.wasm')
        T.assemble(module,src);T.transform(src,dst)
        boundary.append({'shift':s,'offsets':offsets,'original':src.name,'projected':dst.name})
    (out/'boundary-input.json').write_text(json.dumps(boundary,indent=2),encoding='utf-8')
    script='''const fs=require('fs'),path=require('path');const dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'boundary-input.json')));let checks=0,bad=0,traps=0;
const mem=new Uint8Array(65536);for(let i=0;i<32;i++)mem[i]=i;mem.set([1,2,3,4,5,6,7,8],65528);mem[65535]=165;
const details=[];let st=0x651635;const random=()=>{st^=st<<13;st^=st>>>17;st^=st<<5;return st>>>0;};
for(const r of rows){const limit=Math.floor((65535-Math.max(...r.offsets))/2**r.shift);
 const inputs=[...Array.from({length:33},(_,i)=>i),Math.max(0,limit-1),limit,limit+1,0x7fffffff,0x80000000,0xffffffff,...Array.from({length:128},random)];
 for(const file of [r.original,r.projected]){const bytes=fs.readFileSync(path.join(dir,file));if(!WebAssembly.validate(bytes))throw Error('validate');
 const f=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;let failures=0;
 for(const x of inputs){const base=Number((BigInt(x>>>0)*(1n<<BigInt(r.shift)))&0xffffffffn),a=base+r.offsets[0],b=base+r.offsets[1];
 const expected=a>=65536||b>=65536?'trap':mem[a]^mem[b];let got;
 try{got=f(x)>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError)||!/memory access out of bounds/i.test(e.message))throw e;got='trap';traps++;}
 if(got!==expected)failures++;checks++;}bad+=failures;details.push({file,inputs:inputs.length,mismatches:failures});}}
fs.writeFileSync(path.join(dir,'boundaries.json'),JSON.stringify({checks,bad,traps,details},null,2));console.log(JSON.stringify({checks,bad,traps}));if(bad)process.exitCode=1;'''
    (out/'check-boundaries.cjs').write_text(script,encoding='utf-8')
    subprocess.run([shutil.which('node'),str(out/'check-boundaries.cjs'),str(out)],check=True,timeout=30)
    hashes=[]
    sources=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+list(Path(__file__).parent.glob('*.md'))
    sources += [T.ROOT/'research/observation-synthesis'/x for x in ['transform.py','core.py']]
    for p in sources:
        rel=p.relative_to(T.ROOT);dest=out/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        hashes.append({'path':rel.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result={'WABT_version':T.W.tool('wasm-interp',['--version']).strip(),'second_engine_executions':len(checked),
        'mismatches':sum(not r['equal'] for r in checked),'records':checked,'rank_tests':rank_tests,
        'contradiction_rejected':contradiction_rejected,'source_hashes':hashes,
        'manifest_sha256':hashlib.sha256((run/'manifest.json').read_bytes()).hexdigest()}
    (out/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['records','rank_tests','source_hashes','manifest_sha256']}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();main(args.run,args.output)
