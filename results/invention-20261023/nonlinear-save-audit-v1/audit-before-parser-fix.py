import itertools, json, random, re, sys
from pathlib import Path
import prototype as p

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    spaces=p.m.subspaces(3);hist={};better=0;count=0
    for enc in itertools.permutations(range(8)):
        info=p.m.plan(3,[(0,1,1),(1,2,1)],list(enc));linear=p.m.linear_save(info,spaces);count+=1
        key='%d/%d'%(info['color_bits'],linear['color_bits']);hist[key]=hist.get(key,0)+1;better+=info['color_bits']<linear['color_bits']
    p.q.save(out/'exhaustive.json',{'permutations':count,'copy_sequence':[[0,1,1],[1,2,1]],'color_bits_linear_bits':hist,'strict_gain':better,'subspaces':len(spaces)})
    patterns=[[(1,0,1),(2,1,2)],[(0,1,2),(2,0,2)],[(3,0,1),(1,2,1),(2,0,1)]];spaces=p.m.subspaces(4);held=[]
    for i,ops in enumerate(patterns):
        for k in range(200):
            seed=220000+i*200+k;enc=list(range(16));random.Random(seed).shuffle(enc);info=p.m.plan(4,ops,enc);linear=p.m.linear_save(info,spaces)
            held.append({'pattern':i,'seed':seed,'color_bits':info['color_bits'],'linear_bits':linear['color_bits'],'colors':info['color_count']})
    p.q.save(out/'holdout.json',{'cases':len(held),'strict_gain':sum(r['color_bits']<r['linear_bits'] for r in held),'rows':held,'used_for_benchmark_selection':False})
    cases=json.loads((folder/'cases.json').read_text());rows=json.loads((folder/'manifest.json').read_text());cross=[]
    for row in rows:
        if row.get('negative'):continue
        src=folder/row['file'];mod=p.q.read(src);exports={e[1].strip('"'):int(e[2][1]) for e in mod[1:] if e[0]=='export'}
        # Exports are executed in declaration order; after a trap the next probe observes memory.
        wrappers=[];expected=[]
        for x in (0,15,5):
            for fail in range(len(cases[row['name']]['ops'])+1):
                j=len(expected);wrappers.append('(func (export "init%d") (call %d %s))'%(j,exports['reset'],p.c(x)))
                wrappers.append('(func (export "run%d") (call %d %s))'%(j,exports['run'],p.c(fail)))
                wrappers.append('(func (export "peek%d") (result i32) (call %d))'%(j,exports['peek']))
                y=x
                for op in cases[row['name']]['ops'][:fail]:y=p.m.copy(y,op,4)
                expected.append({'value':y,'trap':fail<len(cases[row['name']]['ops'])})
        # Remove original no-arg peek export so only named probes are parsed.
        mod=[mod[0],*[e for e in mod[1:] if e[0]!='export']]
        f=out/(src.stem+'-interp.wasm');p.q.compile(p.q.w.emit(mod)[:-1]+''.join(wrappers)+')',f)
        log=p.q.w.tool('wasm-interp',[f,'--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[int(x) for x in re.findall(r'peek\d+\(\) => i32:(\d+)',log)];runs=re.findall(r'run\d+\(\) => ([^\n]*)',log)
        assert got==[r['value'] for r in expected],(row,got,expected)
        assert len(runs)==len(expected) and [('error:' in x) for x in runs]==[r['trap'] for r in expected],runs
        cross.append({'file':row['file'],'runs':len(expected),'expected_traps':sum(r['trap'] for r in expected),'values':got})
    rejected=[]
    base=p.plain(patterns[0])
    for name,text in [('memory-export',base.replace('(memory 1 1)','(memory (export "memory") 1 1)')),('extra-global',base.replace('(module','(module (global (mut i32) (i32.const 0))',1)),('wrong-peek',base.replace('(func (export "peek") (result i32) '+p.pack()+')','(func (export "peek") (result i32) (i32.const 0))'))]:
        f=out/(name+'.wasm');p.q.compile(text,f)
        try:p.parse(f)
        except ValueError as exc:rejected.append({'case':name,'reason':str(exc)})
        else:raise AssertionError('invalid profile accepted')
    result={'permutations':count,'strict_gain_exhaustive':better,'holdout_cases':len(held),'holdout_strict_gain':sum(r['color_bits']<r['linear_bits'] for r in held),'wabt':cross,'wabt_runs':sum(r['runs'] for r in cross),'wabt_expected_traps':sum(r['expected_traps'] for r in cross),'rejected':rejected}
    p.q.save(out/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('wabt','rejected')}))
if __name__=='__main__':main(*sys.argv[1:])
