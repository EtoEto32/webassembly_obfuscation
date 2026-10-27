import argparse,json,re,shutil
from pathlib import Path
import prototype as p
import guarded as g


def audit(main,perf,out):
    main,perf,out=map(lambda x:Path(x).resolve(),(main,perf,out));out.mkdir(parents=True,exist_ok=False)
    verified={}
    for folder in (main,perf):
        pins=json.loads((folder/'pins.json').read_text(encoding='utf-8'))
        for name,h in pins.items():assert p.q.digest(folder/name)==h,name
        verified[folder.name]=len(pins)
    g.run(out/'reproduction');m=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    for t in m['targets']:assert (main/t['file']).read_bytes()==(out/'reproduction'/t['file']).read_bytes(),t['file']
    analyses=json.loads((main/'analysis.json').read_text(encoding='utf-8'));transcripts=[]
    for name in m['fixtures']:
        rows=[a for a in analyses if a['name']==name]
        assert all(a['query']['samples']==rows[0]['query']['samples'] for a in rows)
        transcripts.append(dict(name=name,conditions=len(rows),queries_each=34,transcripts_equal=True))
    xs=[0,1,2,7,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa];rows=[]
    for t in m['targets']:
        mod=p.q.read(main/t['file']);index=next(e[2][1] for e in mod[1:] if e[0]=='export')
        for i,x in enumerate(xs):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call',index,['i32.const',str(x)]]])
        file=out/'wabt'/t['file'];p.q.compile(p.q.w.emit(mod),file)
        stdout=p.q.w.tool('wasm-interp',[file,'--run-all-exports']);file.with_suffix('.log').write_text(stdout,encoding='utf-8')
        for i,x in enumerate(xs):
            lines=[v for v in stdout.splitlines() if v.startswith('case'+str(i)+'()')]
            assert len(lines)==1 and re.search(r'=> i32:'+str(p.evaluate(m['fixtures'][t['name']],x))+r'\s*$',lines[0]),stdout
        rows.append(dict(file=t['file'],calls=len(xs),mismatches=0))
    p.q.save(out/'wabt.json',rows)
    result=dict(verified_pins=verified,reproduced_targets=len(m['targets']),unique_positive_binaries=len({t['sha256'] for t in m['targets']}),wabt_calls=sum(r['calls'] for r in rows),transcript_comparisons=transcripts,limitations='Reproduction repeats do not add independent cases; the public attack relies on the polynomial-function promise.')
    p.q.save(out/'audit.json',result)
    srcdir=out/'sources';srcdir.mkdir()
    for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,srcdir/'__'.join(f.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(result))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('performance');ap.add_argument('output');a=ap.parse_args();audit(a.main,a.performance,a.output)
