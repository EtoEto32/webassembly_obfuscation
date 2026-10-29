"""Generic Spacer reachability baseline for a concrete two-store initial state.

This is our CHC encoding, not the Whisk/WasmVerifier author implementation.
Effects use independent symbolic arrays, not synthesis copy maps or its layers.
"""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load('contract','guard-contract.py');a=load('symbolic','guard-project-check.py');z=a.z

def encode(model,left,right,values,contract,protocol,timeout=5000):
    ns,nc=len(model['segments']),len(model['cells']);lf=[z.Bool('lflag'+str(i)) for i in range(ns)];rf=[z.Bool('rflag'+str(i)) for i in range(ns)]
    lv=[z.Int('lcell'+str(i)) for i in range(nc)];rv=[z.Int('rcell'+str(i)) for i in range(nc)];variables=lf+rf+lv+rv
    relation=z.Function('State',*([z.BoolSort()]*(2*ns)+[z.IntSort()]*(2*nc)+[z.BoolSort()]));bad=z.Function('Bad',z.BoolSort())
    fp=z.Fixedpoint();fp.set(engine='spacer',timeout=timeout);fp.register_relation(relation,bad)
    if variables:fp.declare_var(*variables)
    initial=[z.BoolVal(v) for v in left+right]+[z.IntVal(values[i]) for i in model['cells']]*2;fp.rule(relation(*initial))
    current=relation(*variables);la=ra=z.K(z.IntSort(),z.IntVal(0))
    for i,l,r in zip(model['cells'],lv,rv):la=z.Store(la,i,l);ra=z.Store(ra,i,r)
    observed=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    visible=[i for i in model['cells'] if i//c.g.BASE in observed]
    for ai,action in enumerate(model['actions']):
        af,an,am=a.execute(model,lf,action,la);bf,bn,bm=a.execute(model,rf,action,ra)
        same=[an==bn]+[z.Select(am,i)==z.Select(bm,i) for i in visible]
        if action['observation']=='read-byte':same += [z.Select(la,i)==z.Select(ra,i) for i in model['cells'] if i<c.g.BASE]
        eq=z.simplify(z.And(*same));continues=z.BoolVal(True) if protocol=='reenter' else z.Or(an,bn)
        if protocol=='terminal' and action['observation']=='read-byte' and model['resources'][0]['length']==0:continues=z.BoolVal(False)
        head=af+bf+[z.Select(am,i) for i in model['cells']]+[z.Select(bm,i) for i in model['cells']]
        fp.rule(bad(),[current,z.Not(eq)],name='observe_'+str(ai));fp.rule(relation(*[z.simplify(v) for v in head]),[current,eq,z.simplify(continues)],name='step_'+str(ai))
    return fp,bad

def main(source,out,max_cells=32,only_unsupported=None):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());rows=[]
    selected=None if only_unsupported is None else {(r['name'],r['sample']) for r in json.loads(only_unsupported.read_text())['rows'] if r['status']=='unsupported-footprint'}
    try:
        for ri,row in enumerate(manifest['rows']):
            model=c.parse(k.p.read(source/row['source']));contract=row['proof']['contract'];protocol=manifest.get('protocol','reenter')
            for si,sample in enumerate(row['samples']):
                if selected is not None and (row['name'],si) not in selected:continue
                result={'name':row['name'],'sample':si,'contract':contract,'protocol':protocol,'cells':len(model['cells']),'expected':'sat' if sample['witness'] else 'unsat'};rows.append(result)
                if len(model['cells'])>max_cells:result.update(status='unsupported-footprint',reason='more than '+str(max_cells)+' cells');continue
                values={i:0 if i<c.g.BASE else 256 for i in model['cells']};values.update(dict(sample['patches']));start=time.perf_counter()
                try:
                    fp,bad=encode(model,row['left'],row['right'],values,contract,protocol);result['encodingSeconds']=time.perf_counter()-start
                    smt=out/f'query-{ri:02}-{si}.smt2';smt.write_text(fp.sexpr()+'\n(query Bad)\n');result['smt']=smt.name;start=time.perf_counter()
                    try:
                        answer=fp.query(bad());result.update(status=str(answer),querySeconds=time.perf_counter()-start)
                        if answer==z.unknown:result['reason']=fp.reason_unknown()
                    except z.Z3Exception as e:
                        message=str(e);result.update(status='timeout' if 'canceled' in message.lower() or 'timeout' in message.lower() else 'solver-error',reason=message,querySeconds=time.perf_counter()-start)
                except Exception as e:result.update(status='encoder-error',reason=repr(e))
                if result['status'] in ('sat','unsat'):assert result['status']==result['expected'],result
            if ri%6==5:print(json.dumps({'contractsDone':ri+1,'queries':len(rows),'timeouts':sum(r['status']=='timeout' for r in rows)}),flush=True)
        counts={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
        result={'rows':rows,'counts':counts,'z3':z.get_version_string(),'perQueryTimeoutMs':5000,'maxCells':max_cells,'selectedFrom':str(only_unsupported) if only_unsupported else None,
          'scope':'Concrete-state reachability using our standard Spacer encoding; shared parser and independent symbolic array effects; not an author-tool reproduction or precondition synthesis.'}
        (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'counts':counts}))
    except Exception as e:
        (out/'failure.json').write_text(json.dumps({'reason':repr(e),'rows':rows},indent=2));raise
    finally:
        for n in ('guard-chc.py','guard-contract.py','guard-project-check.py','guard-project.py','guard-witness.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
        (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--max-cells',type=int,default=32);p.add_argument('--only-unsupported',type=Path);v=p.parse_args()
    if not 1<=v.max_cells<=256:p.error('max-cells must be 1..256')
    main(v.source,v.out,v.max_cells,v.only_unsupported)
