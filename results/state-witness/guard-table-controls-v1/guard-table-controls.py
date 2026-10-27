"""Generate table/cross-table controls and seeded equality-guard inputs."""
import argparse,hashlib,importlib.util,json,random,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('table_guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def api(name,body):return f'(func (export "{name}") {body})'
def init(seg,table=0,dst=0,src=0,n=1):return f'(table.init {table} {seg} (i32.const {dst}) (i32.const {src}) (i32.const {n}))'
def copy(dst,src,n=1,dt=0,st=0):return f'(table.copy {dt} {st} (i32.const {dst}) (i32.const {src}) (i32.const {n}))'
def fill(ref):return f'(table.fill 0 (i32.const 0) {ref} (i32.const 1))'
def main(out):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(261024);rows=[]
    masked=api('test',init(0)+'(elem.drop 0)'+init(2));t=lambda i:g.cell(1,i);u=lambda i:g.cell(2,i)
    eq=lambda cells:[[['c',257],['m',i]] for i in sorted(cells)]
    fixtures=[
      ('masked',masked,eq([t(0)])),
      ('copy',masked+api('copy',copy(0,1)),eq([t(0),t(1)])),
      ('overlap',masked+api('copy',copy(0,1,3)),eq([t(i) for i in range(4)])),
      ('cross-table',masked+api('copy',copy(0,1,1,0,1)),eq([t(0),u(1)])),
      ('null-fill',masked+api('fill',fill('(ref.null func)')),None),
      ('same-fill',masked+api('fill',fill('(ref.func $a)')),eq([t(0)])),
      ('other-fill',masked+api('fill',fill('(ref.func $b)')),None),
      ('drop-first',api('test','(elem.drop 0)'+init(0)),[]),
      ('zero-end',api('test',init(0,dst=4,n=0)),[]),
      ('zero-source-one',api('test',init(0,src=1,n=0)),None),
      ('unsigned-oob',api('test',init(0,dst=-1)),[]),
      ('mixed-memory',api('test','(memory.fill (i32.const 1) (i32.const 66) (i32.const 2))'+init(0)+'(elem.drop 0)'+init(2)),eq([t(0)])),
    ]
    for name,body,expected in fixtures:
        src=out/(name+'.wasm');k.p.compile_wat('''(module (memory 1 1) (table 4 4 funcref) (table 4 4 funcref)
          (func $a (result i32) (i32.const 101)) (func $b (result i32) (i32.const 202))
          (elem func $a) (elem func $b) (elem func $a) '''+body+')',src)
        m=k.p.read(src);model=g.parse(m);left,right=[False,True,False],[True,True,False];proof=g.solve(model,left,right)
        assert proof['guard']==expected,(name,proof['guard'],expected)
        for r,info in model['resources'].items():
            kind=info['kind'];i=info.get('index',0);m.append(k.p.expr(f'(export "__guard_resource_{r}" ({kind} {i}))'))
        for i in range(model['functions']):m.append(k.p.expr(f'(export "__guard_func_{i}" (func {i}))'))
        for i,s in enumerate(model['segments']):m.append(k.p.expr(f'(func (export "__guard_drop_{i}") ({s["kind"]}.drop {s["index"]}))'))
        prepared=out/(name+'-prepared.wasm');k.p.compile_wat(k.p.w.emit(m),prepared)
        samples=[]
        for si in range(12):
            values={i:rng.randrange(256) if i<g.BASE else rng.choice([256,257,258]) for i in model['cells']}
            if si<6 and expected is not None:
                for x,y in expected:values[y[1]]=x[1] if x[0]=='c' else values[x[1]]
            val=lambda x:x[1] if x[0]=='c' else values[x[1]]
            positive=expected is not None and all(val(x)==val(y) for x,y in expected)
            samples.append({'patches':[[i,v] for i,v in sorted(values.items())],'satisfies':positive})
        rows.append({'name':name,'source':src.name,'prepared':prepared.name,'proof':proof,'left':left,'right':right,
          'actions':[a['name'] for a in model['actions'] if not a['readonly']],'samples':samples})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'depth':4,'seed':261024},indent=2))
    for n in ('guard-table-controls.py','guard-table-controls.mjs','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    p=subprocess.run(['node',str(out/'guard-table-controls.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));assert p.returncode==0,p.stderr;print(p.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
