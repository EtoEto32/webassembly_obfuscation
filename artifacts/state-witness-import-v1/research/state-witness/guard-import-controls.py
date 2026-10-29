"""Generate real import-bearing modules; check conditions and SMT witnesses."""
import argparse,hashlib,importlib.util,itertools,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('import_check',HERE/'guard-import-check.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);i=q.i
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def program(kind,mode):
    touch='(call $touch)'
    if kind=='memory':
        decl='(memory (export "resource") 1 1) (data "A") (data "B") (data (i32.const 0) "A")'
        init='(memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1))';zero=init.replace('(i32.const 1)','(i32.const 0)')
        fail='(memory.init 1 (i32.const 0) (i32.const 2) (i32.const 1))';repair='(memory.fill (i32.const 0) (i32.const 65) (i32.const 1))';drop='data.drop'
    else:
        decl='(table (export "resource") 2 2 funcref) (func $a (result i32) (i32.const 101)) (func $b (result i32) (i32.const 202)) (elem func $a) (elem func $b) (elem (i32.const 0) func $a $b)'
        init='(table.init 0 (i32.const 0) (i32.const 0) (i32.const 1))';zero=init.replace('(i32.const 1)','(i32.const 0)')
        fail='(table.init 1 (i32.const 0) (i32.const 2) (i32.const 1))';repair='(table.fill (i32.const 0) (ref.func $a) (i32.const 1))';drop='elem.drop'
    body={'before':touch+init+fail,'after':init+touch+fail,'repair':touch+repair+init+fail,'zero':touch+zero+fail,
          'twice':touch+repair+touch+init+fail,'unreachable':fail+touch+init}.get(mode)
    if body is None:
        body='(func (export "arm") '+init+fail+') (func (export "finish") '+(touch+repair if mode=='read-before-repair' else repair+touch)+fail+')'
    else:body='(func (export "entry") '+body+')'
    return f'(module (import "env" "touch" (func $touch)) {decl} (func (export "retire") ({drop} 0) ({drop} 1)) (func (export "release_b") ({drop} 1)) {body})'


def replay(engine,compiled,row,values,word):
    counts={'apiCalls':0,'preparationCalls':0,'hostCalls':0,'cellWrites':0,'pureTagCalls':0};runs=[]
    with wt.Store(engine) as store:
        for side in range(2):
            ex={};refs={};trace=[];current={};block=0
            def snap():
                if row['kind']=='memory':return list(ex['resource'].read(store,0,2))
                result=[]
                for n in range(2):
                    ref=ex['resource'].get(store,n)
                    if not isinstance(ref,wt.Func):result.append(256)
                    else:result.append({101:258,202:259,303:260}[ref(store)]);counts['pureTagCalls']+=1
                return result
            def host():
                nonlocal block
                event={'name':'env.touch'};summary=row['proof']['hostSummaries'][0]
                if summary['reads']=='public':event['read']=snap()
                trace.append(event);counts['hostCalls']+=1
                writes=current.get(block,{})
                if summary['writes']=='public':
                    for cell,value in writes.items():
                        if row['kind']=='memory':ex['resource'].write(store,bytes([value]),cell)
                        else:ex['resource'].set(store,cell%i.g.BASE,refs.get(value))
                        counts['cellWrites']+=1
                block+=1
            f=wt.Func(store,wt.FuncType([],[]),host);ex=wt.Instance(store,compiled,[f]).exports(store)
            if row['kind']=='table':
                refs={256:None,258:ex['resource'].get(store,0),259:ex['resource'].get(store,1),260:wt.Func(store,wt.FuncType([],[wt.ValType.i32()]),lambda:303)}
            ex['retire' if side==0 else 'release_b'](store);counts['preparationCalls']+=1
            for cell,value in values.items():
                if row['kind']=='memory':ex['resource'].write(store,bytes([value]),cell)
                else:ex['resource'].set(store,cell%i.g.BASE,refs[value])
            outputs=[]
            for call in word:
                current={r['block']:dict(r['cells']) for r in call['writes']};block=0;trace=[]
                try:ex[call['name']](store);outcome='return'
                except wt.Trap:outcome='trap'
                counts['apiCalls']+=1
                outputs.append({'name':call['name'],'outcome':outcome,'hostTrace':trace.copy(),'public':snap() if row['proof']['contract']!='returns' else None})
                if outcome=='trap' and row['proof']['protocol']=='terminal':break
            runs.append(outputs)
    return {'equal':runs[0]==runs[1],'traces':runs},counts


def main(out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[];totals={k:0 for k in ('apiCalls','preparationCalls','hostCalls','cellWrites','pureTagCalls')};checks=0
    modes=('before','after','repair','zero','twice','unreachable','read-before-repair','read-after-repair')
    for kind,mode in itertools.product(('memory','table'),modes):
        raw=out/(kind+'-'+mode+'.wasm');i.k.p.compile_wat(program(kind,mode),raw);i.k.p.tool('wasm-validate',[raw]);compiled=wt.Module(engine,raw.read_bytes())
        for reads,writes,contract,protocol in itertools.product(('none','public'),('none','public'),('public','returns'),('terminal','reenter')):
            summaries={('env','touch'):{'reads':reads,'writes':writes}};model=i.parse(i.k.p.read(raw),summaries);left=[False,False,False];right=[True,False,False]
            prepared=i.prepare(model,left,right,contract,protocol);name='-'.join((kind,mode,reads,writes,contract,protocol))
            row={'name':name,'kind':kind,'mode':mode,'source':raw.name,'left':left,'right':right,'proof':prepared['proof'],'samples':[]}
            # Constant-matching and contrasting stores, independent of the result.
            for initial in ([65,0] if kind=='memory' else [258,256]):
                values={cell:initial for cell in model['cells']};witness=q.witness(prepared,values);words=[]
                if witness:words.append(witness['calls'])
                else:
                    names=[a['name'] for a in model['actions'] if a['name'] not in ('retire','release_b')]
                    for value in ([0,65,255] if kind=='memory' else [256,258,260]):
                        word=[]
                        for name0 in names:
                            action=next(a for a in model['actions'] if a['name']==name0)
                            word.append({'name':name0,'writes':[{'block':n,'cells':[[cell,value] for cell in model['cells'] if cell//i.g.BASE in model['publicResources']]} for n,b in enumerate(action['blocks']) if b['host'] is not None]})
                        words.append(word)
                traces=[]
                for word in words:
                    run,count=replay(engine,compiled,row,values,word)
                    assert run['equal']==(witness is None),(row['name'],values,word,run)
                    traces.append({'word':word,**run});checks+=1
                    for key,value in count.items():totals[key]+=value
                row['samples'].append({'values':sorted(values.items()),'witness':witness,'runs':traces})
            rows.append(row)
        print(json.dumps({'module':kind+'-'+mode,'contracts':len(rows)}),flush=True)
    result={'rows':rows,'contracts':len(rows),'runtimeComparisons':checks,**totals}
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    run=subprocess.run(['node',str(HERE/'guard-import-controls.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for name0 in ('guard-import-controls.py','guard-import-controls.mjs','guard-import-check.py','guard-import.py','guard-import-plan.md','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name0,out/name0)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
