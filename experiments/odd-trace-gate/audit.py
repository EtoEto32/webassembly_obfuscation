import json,platform,re,subprocess,sys
from pathlib import Path
import gate as g
def main(src,out):
    src=Path(src).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    checks=json.loads((src/'checks.json').read_text());model=json.loads((src/'model.json').read_text());attacks=json.loads((src/'recovery.json').read_text());targets=json.loads((src/'targets.json').read_text())
    assert checks['odd_correct']==checks['recovered_correct']==checks['trace_checks']==804
    assert checks['even_negative_conditions']==6 and model['cases']==882 and model['odd_cases']==378
    assert len(attacks)==6 and all(x['status']=='recovered' for x in attacks)
    assert len({x['output_sha256'] for x in attacks})==1
    probes=[];byte_replay=[]
    for row in targets:
        if row['length']%2==0 or row['opt']!='O3':continue
        for role,old in [('protected',row['path']),('recovered',row['recovered'])]:
            m=g.q.read(old);fs=[e for e in m[1:] if e[0]=='func'];ix=int(next(e[2][1] for e in m[1:] if e[0]=='export' and e[1]=='"run"'))
            fn=['func',['result','i32'],['call',str(ix),['i32.const','-2147483648'],['i32.const','0'],['i32.const','1'],['i32.const','0']]]
            m.extend([fn,['export','"probe"',['func',str(len(fs))]]]);f=out/f'L{row["length"]}-{role}.wasm';g.q.compile(g.q.w.emit(m),f)
            log=g.q.w.tool('wasm-interp',[f,'--run-all-exports']);match=re.search(r'probe\(\) => i32:(\d+)',log);assert match and int(match[1])==2**31
            probes.append({'length':row['length'],'role':role,'value':int(match[1]),'log':log})
        raw=out/f'L{row["length"]}-raw.wasm';opt=out/f'L{row["length"]}-O3.wasm';g.q.compile(g.source(row['length']),raw);g.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt]);assert g.q.digest(opt)==g.q.digest(row['path']);byte_replay.append({'length':row['length'],'O3_match':True})
    direct=out/'plain.wasm';g.q.compile('(module (func (export "run") (param i32 i32 i32 i32) (result i32) (i32.mul (i32.add (local.get 0) (local.get 1)) (i32.sub (local.get 2) (local.get 3)))))',direct)
    result={'scope':'early gate, not a full novel-obfuscator evaluation','checks':{k:checks[k] for k in ('odd_correct','recovered_correct','trace_checks','even_negative_conditions')},'model_cases':882,'model_odd_cases':378,'cross_engine':probes,'byte_replay':byte_replay,'all_recovered_byte_identical':True,'plain_bytes':direct.stat().st_size,'recovered_bytes':52,'platform':platform.platform(),'python':sys.version,'node':checks['node'],'v8':checks['v8'],'wabt':g.q.w.tool('wasm-validate',['--version']).strip(),'binaryen':g.q.tool('wasm-opt',['--version']).strip()}
    files=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+list(Path(__file__).parent.glob('*.md'))
    files.extend(x for x in src.iterdir() if x.suffix in ('.wasm','.json'));files.extend(x for x in out.iterdir() if x.suffix=='.wasm')
    files.extend(g.ROOT/f for f in ('research/isotope-swizzle/prototype.py','research/connectivity-elimination/prototype.py'))
    result['pins']=[{'file':str(f.resolve().relative_to(g.ROOT)),'sha256':g.q.digest(f)} for f in files]
    (out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'model_cases':882,'cross_engine':len(probes),'byte_replay':len(byte_replay),'pins':len(files),'plain_bytes':result['plain_bytes']}))
if __name__=='__main__':main(*sys.argv[1:])
