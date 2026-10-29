import itertools,json,re,subprocess,sys,time
from pathlib import Path
import prototype as p

def partitions(n):
    def go(xs):
        if len(xs)==n:yield xs;return
        for k in range(max(xs)+2):yield from go(xs+[k])
    return list(go([0]))
def lumpable(a,classes):
    signatures={}
    for i,row in enumerate(a):
        sig=tuple(sum(w for j,w in enumerate(row) if classes[j]==c) for c in range(max(classes)+1))
        if classes[i] in signatures and signatures[classes[i]]!=sig:return False
        signatures[classes[i]]=sig
    return True
def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    count=0;relations=0;bad_witness=None
    for n in range(2,6):
        choices=[[(i,i)]+list(itertools.combinations_with_replacement(range(i+1,n),2)) for i in range(n)]
        for edges in itertools.product(*choices):
            a=[[sum(j==v for v in pair) for j in range(n)] for pair in edges];s=p.square(a)
            assert p.root_matrix(s)==a;count+=1
            bad=[[sum(a[i][k]*a[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
            for classes in partitions(n):
                x,y=lumpable(a,classes),lumpable(s,classes);relations+=1
                assert x==y
                if bad_witness is None and x!=lumpable(bad,classes):bad_witness={'a':a,'square_without_laziness':bad,'classes':classes,'original_lumpable':x}
    p.q.save(out/'model.json',{'graphs':count,'partition_checks':relations,'mismatches':0,'bad_witness':bad_witness})
    sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'));import z3
    word=z3.BitVec('word',32)
    def original(t):
        if t[0]=='bit':
            b=z3.Extract(t[1],t[1],word)==1;return z3.Not(b) if t[2] else b
        return (z3.And if t[0]=='and' else z3.Or)(original(t[1]),original(t[2]))
    cases=json.loads((folder/'cases.json').read_text());manifest=json.loads((folder/'manifest.json').read_text())
    proofs=[];cross=[]
    for r in manifest:
        if r.get('negative'):continue
        src=folder/r['file']
        if r['mode'] in ('base','square'):
            labels,a,roots=p.extracted(src)
            if r['mode']=='square':a=p.root_matrix(a)
            bdd,root,_=p.decode(labels,a,roots);memo={0:z3.BoolVal(False),1:z3.BoolVal(True)}
            def term(i):
                if i not in memo:
                    bit,lo,hi=bdd.nodes[i];memo[i]=z3.If(z3.Extract(bit,bit,word)==1,term(hi),term(lo))
                return memo[i]
            solver=z3.Solver();solver.set(timeout=10000);solver.add(term(root)!=original(cases[r['name']]['tree']));verdict=str(solver.check());assert verdict=='unsat'
            proofs.append({'file':r['file'],'verdict':verdict,'scope':'source Boolean AST versus extracted BDD, not whole compiler'})
        m=p.q.read(src);xs=[0,0xffffffff,0x12345678]
        wrappers=''.join(f'(func (export "probe{i}") (result i32) (call 0 (i32.const {x})))' for i,x in enumerate(xs))
        target=out/(src.stem+'-interp.wasm');p.q.compile(p.q.w.emit(m)[:-1]+wrappers+')',target)
        log=p.q.w.tool('wasm-interp',[target,'--run-all-exports']);(target.with_suffix('.log')).write_text(log,encoding='utf-8')
        got=[int(x) for x in re.findall(r'probe\d+\(\) => i32:(\d+)',log)];assert len(got)==len(xs)
        expected=[int(z3.is_true(z3.simplify(z3.substitute(original(cases[r['name']]['tree']),(word,z3.BitVecVal(x,32)))))) for x in xs]
        assert got==expected,(r,got,expected)
        cross.append({'file':r['file'],'inputs':xs,'expected':expected,'actual':got})
    rejected=[]
    for label,wat in [('source-memory','(module (memory 1) (func (export "run") (param i32) (result i32) (local.get 0)))'),('source-add','(module (func (export "run") (param i32) (result i32) (i32.add (local.get 0) (i32.const 1))))')]:
        f=out/(label+'.wasm');p.q.compile(wat,f)
        try:p.source(f)
        except ValueError as e:rejected.append({'case':label,'reason':str(e)})
        else:raise AssertionError('unsupported source accepted')
    labels,a,roots=p.graph(p.source(folder/'bits4-plain-raw.wasm'),213071)
    modified=p.render(labels,p.square(a),roots).replace('(local.set $n','(i32.store (i32.const 0) (i32.const 0)) (local.set $n',1)
    f=out/'altered-evaluator.wasm';p.q.compile(modified,f)
    try:p.extracted(f)
    except ValueError as e:rejected.append({'case':'altered-evaluator','reason':str(e)})
    else:raise AssertionError('altered evaluator accepted')
    p.q.save(out/'audit.json',{'model_graphs':count,'model_partition_checks':relations,'smt':proofs,'wabt_calls':len(cross)*3,'wabt':cross,'rejected_controls':rejected,'z3':z3.get_version_string()})
    print(json.dumps({'graphs':count,'partitions':relations,'smt_unsat':len(proofs),'wabt_calls':len(cross)*3,'rejected_controls':len(rejected)}))
if __name__=='__main__':main(*sys.argv[1:])
