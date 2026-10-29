"""Concrete-state Spacer baseline with arbitrary shared public write inputs."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('baseline',HERE/'guard-chc.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);z=b.z

def encode(model,left,right,values,contract,protocol):
    fp,bad=b.encode(model,left,right,values,contract,protocol)
    ns,nc=len(model['segments']),len(model['cells'])
    flags=[z.Bool('envflag'+str(i)) for i in range(2*ns)]
    lv=[z.Int('envleft'+str(i)) for i in range(nc)];rv=[z.Int('envright'+str(i)) for i in range(nc)]
    relation=z.Function('State',*([z.BoolSort()]*(2*ns)+[z.IntSort()]*(2*nc)+[z.BoolSort()]))
    updated_left=lv.copy();updated_right=rv.copy();inputs=[];domain=[]
    for i,cell in enumerate(model['cells']):
        if cell//b.c.g.BASE not in model['publicResources']:continue
        value=z.Int('environmentInput'+str(i));inputs.append(value)
        domain.append(z.And(value>=0,value<=255) if cell<b.c.g.BASE else value>=256)
        updated_left[i]=value;updated_right[i]=value
    variables=flags+lv+rv+inputs
    if variables:fp.declare_var(*variables)
    fp.rule(relation(*(flags+updated_left+updated_right)),[relation(*(flags+lv+rv)),*domain],name='common_public_assignment')
    return fp,bad

def main(source,out,sample_index):
    out.mkdir(parents=True,exist_ok=False);rows=[];cache={}
    try:
        for index,row in enumerate(json.loads((source/'manifest.json').read_text())['rows']):
            if row['source'] not in cache:cache[row['source']]=b.c.parse(b.k.p.read(source/row['source']))
            model=cache[row['source']];sample=row['samples'][sample_index];proof=row['proof'];start=time.perf_counter()
            result={'name':row['name'],'sample':sample_index,'expected':'sat' if sample['witness'] else 'unsat','legacyNegative':sample['legacyNegative']};rows.append(result)
            try:
                fp,bad=encode(model,row['left'],row['right'],dict(sample['patches']),proof['contract'],proof['protocol']);result['encodingSeconds']=time.perf_counter()-start
                smt=out/f'query-{index:03}.smt2';smt.write_text(fp.sexpr()+'\n(query Bad)\n');result['smt']=smt.name;start=time.perf_counter()
                try:
                    answer=fp.query(bad());result.update(status=str(answer),querySeconds=time.perf_counter()-start)
                    if answer==z.unknown:result['reason']=fp.reason_unknown()
                except z.Z3Exception as err:
                    msg=str(err);result.update(status='timeout' if 'canceled' in msg.lower() or 'timeout' in msg.lower() else 'solver-error',reason=msg,querySeconds=time.perf_counter()-start)
            except Exception as err:result.update(status='encoder-error',reason=repr(err))
            if result['status'] in ('sat','unsat'):assert result['status']==result['expected'],result
            if len(rows)%96==0:print(json.dumps({'queries':len(rows),'timeouts':sum(r['status']=='timeout' for r in rows)}),flush=True)
        counts={status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})}
        result={'rows':rows,'counts':counts,'z3':z.get_version_string(),'perQueryTimeoutMs':5000,'sampleIndex':sample_index,
            'scope':'Our generic CHC encoding, same concrete initial inputs, arbitrary common public assignments; not condition synthesis or an author-tool reproduction.'}
        (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(counts))
    except Exception as err:(out/'failure.json').write_text(json.dumps({'reason':repr(err),'rows':rows},indent=2));raise
    finally:
        for name in ('guard-environment-chc.py','guard-chc.py','guard-contract.py','guard-project-check.py','guard-project.py','guard-witness.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);a.add_argument('--sample',type=int,default=2);v=a.parse_args();main(v.source,v.out,v.sample)
