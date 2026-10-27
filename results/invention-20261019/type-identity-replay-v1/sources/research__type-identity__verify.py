import argparse,json,subprocess
from pathlib import Path
import prototype as q

def ref(rows,x,n):
    s=0
    for i in range(n&31):s=rows[s][(x>>i)&1]
    return rows[s][2]
def shell(binary,checks,dst):
    blob=''.join('\\%02x'%b for b in Path(binary).read_bytes())
    script='(module binary "'+blob+'")\n'+'\n'.join(f'(assert_return (invoke "{name}" '+ ' '.join(f'(i32.const {v})' for v in args)+f') (i32.const {expected}))' for name,args,expected in checks)
    dst.write_text(script,encoding='utf-8');log=q.tool('wasm-shell',[dst]);dst.with_suffix('.log').write_text(log,encoding='utf-8')
    return len(checks)
def main(main,out):
    main=Path(main);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((main/'manifest.json').read_text());models=json.loads((main/'models.json').read_text());records=[];count=0
    inputs=[(0,0),(0,31),(1,1),(0x7fffffff,31),(-1,-1),(0x55555555,15)]
    for row in rows:
        for key in ('file','recovered'):
            f=main/row[key];checks=[('run',[x,n],ref(models[row['kernel']],x&0xffffffff,n)) for x,n in inputs]
            n=shell(f,checks,out/(f.stem+'.wast'));count+=n;records.append(dict(file=f.name,checks=n,status='pass'))
    # Cover every state and symbol of each raw GC transition graph, not only states
    # reached by the sampled public run inputs.
    table_checks=0;node_checks=0
    for row in rows:
        if row['opt']!='raw' or row['mode'] not in ('gc','groups'):continue
        m=q.p.w.parse(q.tool('wasm-dis',[main/row['file']]))
        funcs=[x for x in m[1:] if x[0]=='func'];globs=[x for x in m[1:] if x[0]=='global'];model=models[row['kernel']]
        assert len(funcs)==3 and len(globs)==len(model)
        checks=[]
        for i,r in enumerate(model):
            for b in (0,1):
                name=f's{i}b{b}';ty=globs[r[b]][-1][1]
                f=f'(func (export "{name}") (result i32) (ref.test (ref {ty}) (call {funcs[0][1]} (global.get {globs[i][1]}) (i32.const {b}))))'
                m.append(q.p.w.parse('(module '+f+')')[1]);checks.append((name,[],1))
            name=f'a{i}';f=f'(func (export "{name}") (result i32) (call {funcs[1][1]} (global.get {globs[i][1]})))'
            m.append(q.p.w.parse('(module '+f+')')[1]);checks.append((name,[],r[2]))
        f=out/(row['file'][:-5]+'-table.wasm');wat=f.with_suffix('.wat');wat.write_text(q.p.w.emit(m),encoding='utf-8');q.tool('wasm-as',[wat,*q.FEATURES,'-o',f])
        table_checks+=shell(f,checks,f.with_suffix('.wast'))
        checkfile=f.with_suffix('.checks.json');q.save(checkfile,checks)
        script='const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;for(const [n,a,v] of JSON.parse(fs.readFileSync(process.argv[2]))){if(e[n](...a)!==v)throw Error(n)}'
        subprocess.run(['node','-e',script,str(f),str(checkfile)],check=True,timeout=30);node_checks+=len(checks)
    q.save(out/'records.json',records);q.save(out/'summary.json',dict(binaryen_run_checks=count,binaryen_transition_accept_checks=table_checks,node_transition_accept_checks=node_checks,all_pass=True));print(json.dumps(json.loads((out/'summary.json').read_text())))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('main');a.add_argument('output');v=a.parse_args();main(v.main,v.output)
