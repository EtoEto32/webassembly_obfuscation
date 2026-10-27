"""Post-attack scoring only: prove learned scalar formula equals the input expression."""
import json
from pathlib import Path
import sys
from compile import ROOT, read_source
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'))
import z3

root=Path(sys.argv[1]);data=json.loads((root/'io-audit.json').read_text());x,y=z3.BitVecs('x y',32)
def source(e):
    op=e[0]
    if op=='local.get':return [x,y][int(e[1])]
    if op=='i32.const':return z3.BitVecVal(int(e[1]),32)
    a,b=source(e[1]),source(e[2])
    return {'i32.add':lambda:a+b,'i32.and':lambda:a&b,'i32.xor':lambda:a^b,
            'i32.or':lambda:a|b,'i32.rotl':lambda:z3.RotateLeft(a,b)}[op]()
def learned(e):
    if e=='x':return x
    if e=='y':return y
    if isinstance(e,int):return z3.BitVecVal(e,32)
    if e[0]=='rot':return z3.RotateLeft(learned(e[1]),e[2])
    a,b=learned(e[1]),learned(e[2]);return {'add':lambda:a+b,'xor':lambda:a^b,'and':lambda:a&b,'or':lambda:a|b}[e[0]]()
rows=[]
for r in data['rows']:
    n,e=read_source(root/(r['family']+'.wasm'));assert n==2
    s=z3.Solver();s.set(timeout=10000);s.add(source(e)!=learned(r['expression']));ans=str(s.check())
    rows.append({'wasm':r['wasm'],'result':ans,'expression':r['expression']})
    if ans!='unsat':raise AssertionError(ans)
out=root/'io-verified.json'
if out.exists():raise ValueError('Refuse overwrite')
out.write_text(json.dumps({'z3':z3.get_version_string(),'conditions':len(rows),'rows':rows,
    'scope':'Learned formula vs original supported pure i32 expression for all input bitvectors. Does not prove GC compiler correctness.'},indent=2),encoding='utf-8')
print(json.dumps({'conditions':len(rows),'unsat':sum(x['result']=='unsat' for x in rows)}))
