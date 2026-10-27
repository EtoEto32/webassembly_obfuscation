"""Generate actual Wasm and seeded memories to validate synthesized conditions."""
import argparse,hashlib,importlib.util,itertools,json,random,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def api(name,body):return f'(func (export "{name}") {body})'
def init(seg,dst=0,src=0,n=1):return f'(memory.init {seg} (i32.const {dst}) (i32.const {src}) (i32.const {n}))'
def copy(dst,src,n=1):return f'(memory.copy (i32.const {dst}) (i32.const {src}) (i32.const {n}))'
def fill(dst,val,n=1):return f'(memory.fill (i32.const {dst}) (i32.const {val}) (i32.const {n}))'
def fixtures():
    # left segment 0 dead, right segment 0 live; both segment 1 dead.
    masked=api('test',init(0)+'(data.drop 0)'+init(1))
    return [
      ('masked-one',masked,'conditional',[[['c',65],['m',0]]]),
      ('copy-predecessor',masked+api('copy',copy(0,1)),'conditional',[[['c',65],['m',0]],[['c',65],['m',1]]]),
      ('copy-chain',masked+api('copy',copy(0,1))+api('copy2',copy(1,2)),'conditional',[[['c',65],['m',0]],[['c',65],['m',1]],[['c',65],['m',2]]]),
      ('bad-fill',masked+api('write',fill(0,66)),'impossible',None),
      ('good-fill',masked+api('write',fill(0,65)),'conditional',[[['c',65],['m',0]]]),
      ('drop-first',api('test','(data.drop 0)'+init(0)),'unconditional',[]),
      ('unmasked',api('test',init(0)),'impossible',None),
      ('shared-oob',api('test',init(0,65536)),'unconditional',[]),
      ('zero-source',api('test',init(0,65536,0,0)),'unconditional',[]),
      ('zero-nonzero-source',api('test',init(0,0,1,0)),'impossible',None),
      ('overlap',masked+api('copy',copy(0,1,3)),'conditional',[[['c',65],['m',i]] for i in range(4)]),
      ('unsigned-oob',api('test',init(0,-1,0,1)),'unconditional',[]),
    ]
def satisfies(guard,mem):
    if guard is None:return False
    def value(t):return t[1] if t[0]=='c' else mem[t[1]]
    return all(value(x)==value(y) for x,y in guard)
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];rng=random.Random(41829);engine=wt.Engine();calls=0
    for name,body,status,expected in fixtures():
        raw=out/(name+'.wasm');k.p.compile_wat('(module (memory (export "memory") 1 1) (data "A") (data "B") '+body+')',raw)
        model=g.parse(k.p.read(raw));proof=g.solve(model,[False,False],[True,False]);assert proof['status']==status,(name,proof)
        assert proof['guard']==expected,(name,proof['guard'],expected)
        m=k.p.read(raw)
        for i in range(2):m.append(k.p.expr(f'(func (export "__guard_drop_{i}") (data.drop {i}))'))
        dest=out/(name+'-prepared.wasm');k.p.compile_wat(k.p.w.emit(m),dest);compiled=wt.Module(engine,dest.read_bytes())
        actions=[a['name'] for a in model['actions']];sequences=[list(x) for n in range(1,5) for x in itertools.product(actions,repeat=n)]
        samples=[]
        for i in range(18):
            data=bytearray(rng.randrange(256) for _ in range(16))
            if i<6 and proof['guard'] is not None:
                for x,y in proof['guard']:data[y[1]]=x[1] if x[0]=='c' else data[x[1]]
            positive=satisfies(proof['guard'],data);witness=None
            for seq in sequences:
                traces=[]
                for alive in (False,True):
                    with wt.Store(engine) as store:
                        e=wt.Instance(store,compiled,[]).exports(store);e['memory'].write(store,data)
                        e['__guard_drop_1'](store)
                        if not alive:e['__guard_drop_0'](store)
                        trace=[]
                        for a in seq:
                            try:e[a](store);result='return'
                            except wt.Trap:result='trap'
                            calls+=1;trace.append((result,bytes(e['memory'].read(store))))
                        traces.append(trace)
                if traces[0]!=traces[1]:witness=seq;break
            assert (witness is None)==positive,(name,i,positive,witness)
            samples.append({'bytes':list(data),'satisfies':positive,'witness':witness})
        rows.append({'name':name,'source':raw.name,'prepared':dest.name,'actions':actions,'proof':proof,'samples':samples})
        print(json.dumps({'name':name,'status':status,'iterations':proof['iterations'],'samples':len(samples)}),flush=True)
    (out/'manifest.json').write_text(json.dumps({'seed':41829,'rows':rows,'wasmtimeApiCalls':calls,'depth':4},indent=2))
    for name in ('guard-controls.py','guard-controls.mjs','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    proc=subprocess.run(['node',str(out/'guard-controls.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
