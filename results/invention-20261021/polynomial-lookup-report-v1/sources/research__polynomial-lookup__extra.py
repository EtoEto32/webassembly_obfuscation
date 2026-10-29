import json,pathlib,subprocess,sys
import prototype as p
root=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
def save(n,x):(out/n).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
layout=[]
for tag in ('804','480'):
    src=p.ROOT/f'results/invention-20261021/notdec-baseline-v1/list-32-{tag}.wasm'
    dst=out/f'array-layout-{tag}.wasm';p.transform(src,dst,'array')
    assert dst.read_bytes()==(root/'n32-array-raw.wasm').read_bytes()
    layout.append(dict(kind='field-layout',tag=tag,mode='array',same=True))
items=json.loads((root/'n32-oracle.json').read_text())['items']
src=out/'reversed-list.wasm';p.q.compile(p.list_text(list(reversed(items))),src)
for mode in ('array','poly','poly-pruned'):
    dst=out/('reversed-'+mode+'.wasm');p.transform(src,dst,mode)
    assert dst.read_bytes()==(root/('n32-'+mode+'-raw.wasm')).read_bytes()
    layout.append(dict(kind='list-order',mode=mode,same=True))
save('layout-controls.json',layout)
m=p.q.read(root/'n8-poly-raw.wasm');m.extend([['export','"eval"',['func','0']],['export','"memory"',['memory','0']]])
probe=out/'arithmetic-probe.wasm';p.q.compile(p.q.w.emit(m),probe)
code=r'''const fs=require('fs'),assert=require('assert/strict');
const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
const p=4294967291n,edge=[0n,1n,2n,p/2n,p-2n,p-1n],mem=new Uint32Array(api.memory.buffer);let cases=0;
function check(a,x,c){mem[1024]=Number(c);mem[1025]=Number(a);assert.equal(api.eval(4096,2,x),(a*x+c)%p);cases++;}
for(const a of edge)for(const x of edge)for(const c of edge)check(a,x,c);
let seed=271021;function word(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return BigInt(seed>>>0)%p;}
for(let i=0;i<4096;i++)check(word(),word(),word());console.log(JSON.stringify({cases,mismatches:0,seed:271021}));'''
r=subprocess.run(['node','-e',code,str(probe)],capture_output=True,text=True,check=True,timeout=30)
save('arithmetic.json',json.loads(r.stdout));(out/'arithmetic-oracle.cjs').write_text(code,encoding='utf-8')
print(json.dumps(dict(layout_controls=len(layout),arithmetic=json.loads(r.stdout))))
