"""Prospective mixed-resource regression of chosen observations/protocols."""
import argparse,hashlib,importlib.util,json,random,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('protocol','guard-protocol.py');wc=load('cases','guard-witness-cases.py');c=p.c

def main(out):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(0x71024);rows=[];summary=[]
    def operation(kinds):
        kind=rng.choice(kinds);verb=rng.choice(['init','copy','fill','drop','nop'])
        if verb=='nop':return '(nop)'
        if verb=='drop':return f'({"data" if kind=="memory" else "elem"}.drop {rng.randrange(2)})'
        length=rng.randrange(3);limit=65536 if kind=='memory' else 4
        dst=rng.choice([0,1,2,3,limit,limit+1,-1]);src=rng.choice([0,1,2,3,limit,limit+1,-1])
        table=rng.randrange(2)
        if verb=='init':imm=(str(table)+' ' if kind=='table' else '')+str(rng.randrange(2))+' ';middle=f'(i32.const {rng.randrange(4)})'
        elif verb=='copy':imm=f'{table} {rng.randrange(2)} ' if kind=='table' else '';middle=f'(i32.const {src})'
        else:imm=f'{table} ' if kind=='table' else '';middle=rng.choice(['(ref.null func)','(ref.func $a)','(ref.func $b)']) if kind=='table' else f'(i32.const {rng.choice([0,65,255,256,-1])})'
        return f'({kind}.{verb} {imm}(i32.const {dst}) {middle} (i32.const {length}))'
    try:
        for family,kinds in [('memory',['memory']),('table',['table']),('mixed',['memory','table'])]:
            for ci in range(32):
                name=f'{family}-{ci:02}';header=['(func $a (export "a") (result i32) (i32.const 101))','(func $b (export "b") (result i32) (i32.const 202))']
                if 'memory' in kinds:header += ['(memory '+('(export "public_memory") ' if ci%4 in (1,3) else '')+'1 1)','(data "AB")','(data "CD")']
                if 'table' in kinds:
                    for ti in range(2):header.append('(table '+(f'(export "public_table{ti}") ' if (ci+ti)%4 in (2,3) else '')+'4 4 funcref)')
                    header += ['(elem func $a $b)','(elem func $b $a)']
                bodies=[];masked_kind=kinds[(ci//2)%len(kinds)]
                for ai in range(3):
                    ops=[operation(kinds) for _ in range(rng.randint(1,6))]
                    if ci%2 and ai==0:
                        seg='data' if masked_kind=='memory' else 'elem';imm='1 ' if masked_kind=='table' else ''
                        ops=[f'({masked_kind}.init {imm}0 (i32.const 0) (i32.const 0) (i32.const 1))',f'({seg}.drop 0)',f'({masked_kind}.init {imm}1 (i32.const 1) (i32.const 0) (i32.const 1))']+ops
                    bodies.append(f'(func (export "api{ai}") '+ ' '.join(ops)+')')
                if 'memory' in kinds:bodies.append('(func (export "read") (param i32) (result i32) (i32.load8_u (local.get 0)))')
                raw=out/(name+'.wasm');k.p.compile_wat('(module '+' '.join(header+bodies)+')',raw);module=k.p.read(raw);model=c.parse(module)
                left=[rng.choice([False,True]) for _ in model['segments']];right=[rng.choice([False,True]) for _ in model['segments']]
                if ci%2:
                    mask_kind='data' if masked_kind=='memory' else 'elem'
                    for i,s in enumerate(model['segments']):
                        if s['kind']==mask_kind:left[i]=False;right[i]=s['index']==0
                elif left==right:left[0]=not right[0]
                prepared_binary=out/(name+'-prepared.wasm');wc.prepare_module(module,model,prepared_binary)
                read_indices=sorted({0,65536,-1}|{i for i in model['cells'] if i<c.g.BASE})
                def call(action):return {'name':action['name'],'args':[rng.choice(read_indices)] if action['observation']=='read-byte' else []}
                singles=[{'name':action['name'],'args':[i] if action['observation']=='read-byte' else []} for action in model['actions'] for i in (read_indices if action['observation']=='read-byte' else [0])]
                for contract in ('full','public','returns'):
                    for protocol in ('reenter','terminal'):
                        prepared=p.prepare(model,left,right,contract,protocol);proof=prepared['proof'];samples=[]
                        for si in range(4):
                            values={i:rng.randrange(256) if i<c.g.BASE else rng.choice([256,257,258]) for i in model['cells']};origin='random'
                            if si>=2 and proof['guard'] is not None:
                                for a,b in proof['guard']:
                                    assert b[0]=='m';values[b[1]]=a[1] if a[0]=='c' else values[a[1]]
                                origin='condition-fitted';assert c.holds(proof['guard'],values,values)
                            witness=p.extract(prepared,values);sequences=[]
                            if witness is None:sequences=[[s] for s in singles]+[[call(rng.choice(model['actions'])) for _ in range(rng.randint(2,4))] for _ in range(16)]
                            samples.append({'origin':origin,'patches':[[i,v] for i,v in sorted(values.items())],'witness':witness,'positiveSequences':sequences})
                        rows.append({'name':name+'-'+contract+'-'+protocol,'source':raw.name,'prepared':prepared_binary.name,'family':family,'maskedTemplate':bool(ci%2),
                            'proof':proof,'left':left,'right':right,'samples':samples})
                summary.append({'name':name,'family':family,'maskedTemplate':bool(ci%2),'cells':len(model['cells']),'left':left,'right':right})
            print(json.dumps({'family':family,'modules':len(summary),'contracts':len(rows)}),flush=True)
        manifest={'seed':0x71024,'rows':rows,'modules':summary,'scope':'Prospective synthetic controls, half masked templates. Fitted positives distinct from random. Finite positive execution is not a proof.'}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
        proc=subprocess.run(['node',str(HERE/'guard-holdout-replay.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=180)
        (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2));assert proc.returncode==0,proc.stderr;print(proc.stdout)
    except Exception as e:(out/'failure.json').write_text(json.dumps({'reason':repr(e),'modules':summary,'completedContracts':len(rows)},indent=2));raise
    finally:
        for n in ('guard-holdout.py','guard-holdout-replay.mjs','guard-protocol.py','guard-contract.py','guard-witness-cases.py','guard-witness.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
        (out/'sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir()},indent=2))
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('out',type=Path);main(q.parse_args().out)
