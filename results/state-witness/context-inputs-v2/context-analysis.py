"""Conservative def-use certificate for differences in native segment lifetime.

This checks the original program, not a checkpoint transform or its control state.
Classic data-flow analysis; no claim of a new equivalence decision procedure.
"""
import argparse, copy, hashlib, json, shutil
from pathlib import Path
import prototype as k

PURE = {
    'nop', 'drop', 'select', 'local.get', 'local.set', 'local.tee',
    'global.get', 'global.set', 'ref.null', 'ref.func', 'ref.is_null',
    'memory.size', 'memory.grow', 'memory.copy', 'memory.fill',
    'table.size', 'table.grow', 'table.get', 'table.set', 'table.copy', 'table.fill',
}
NUMERIC = {'const','eqz','eq','ne','lt_s','lt_u','gt_s','gt_u','le_s','le_u','ge_s','ge_u',
           'clz','ctz','popcnt','add','sub','mul','div_s','div_u','rem_s','rem_u',
           'and','or','xor','shl','shr_s','shr_u','rotl','rotr',
           'load','load8_s','load8_u','load16_s','load16_u','load32_s','load32_u',
           'store','store8','store16','store32'}


class Unproved(Exception):
    pass


def finite_profile(module):
    """An exact finite-action interface, with one symbolic read-only action class."""
    result=[];funcs=k.p.section(module,'func');types=k.p.section(module,'type')
    for e in k.p.section(module,'export'):
        if e[2][0]!='func':continue
        f=funcs[int(e[2][1])];tid=int(next(x[1] for x in f[1:] if x[0]=='type'));typ=types[tid][1]
        body=[x for x in f[1:] if x[0] not in k.p.DECL]
        if typ==['func',['param','i32'],['result','i32']] and body==[['i32.load8_u',['local.get','0']]]:
            result.append({'name':json.loads(e[1]),'kind':'all-i32-readonly-self-loop'});continue
        if typ!=['func']:return {'status':'unsupported','reason':'signature/body outside exact finite-action profile'}
        for n in body:
            if n[0] in ('data.drop','elem.drop','nop'):continue
            if n[0] not in ('memory.init','table.init','memory.copy','table.copy','memory.fill','table.fill'):
                return {'status':'unsupported','reason':'nonconstant bulk body'}
            args=[x for x in n[1:] if isinstance(x,list)]
            if len(args)!=3 or any(len(x)!=2 or x[0]!='i32.const' for x in args):
                return {'status':'unsupported','reason':'nonconstant bulk operands'}
        result.append({'name':json.loads(e[1]),'kind':'exact-noargs'})
    return {'status':'accepted','actions':result}


def certify(module, differing):
    """Sufficient condition, all numeric args and arbitrary finite API sequences.

    Equal guest memory/table/globals and corresponding own function identities are
    premises. Each API is analysed from the full initial difference set, so a trap
    or a previous call cannot invalidate the induction: drop only removes bits.
    """
    roots = [int(e[2][1]) for e in k.p.section(module,'export') if e[2][0]=='func']
    funcs = k.p.section(module,'func'); checked=[]; active=[]; events=[]
    try:
        # Reuse the closed, numeric, nonshared profile validation; no output emitted.
        k.augment(module, True)
        def seq(nodes, state):
            for n in nodes:
                if state is None: break
                if not isinstance(n,list): raise Unproved('non-folded instruction')
                op=n[0]
                if op in k.p.DECL: continue
                if op=='if':
                    cond=[x for x in n[1:] if isinstance(x,list) and x[0] not in ('then','else','result')]
                    state=seq(cond,state)
                    if state is None: continue
                    branches=[x[1:] for x in n[1:] if isinstance(x,list) and x[0] in ('then','else')]
                    if len(branches)==1: branches.append([])
                    if len(branches)!=2: raise Unproved('if shape')
                    outputs=[seq(b,set(state)) for b in branches]
                    live=[s for s in outputs if s is not None]
                    state=set.union(*live) if live else None
                    continue
                if op=='block':
                    # Branches are rejected below. A simple block has no transfer.
                    state=seq([x for x in n[1:] if isinstance(x,list) and x[0]!='result'],state)
                    continue
                allowed=(op in PURE or op in ('memory.init','table.init','data.drop','elem.drop','call','unreachable')
                         or ('.' in op and op.split('.')[0] in ('i32','i64') and op.split('.')[1] in NUMERIC))
                if not allowed: raise Unproved('unsupported instruction: '+op)
                state=seq([x for x in n[1:] if isinstance(x,list)],state)
                if state is None: continue
                if op=='unreachable': state=None
                elif op=='call': state=func(int(n[1]),state)
                elif op in ('data.drop','elem.drop'):
                    key=(op.split('.')[0],int(n[1]));state.discard(key)
                    events.append({'function':active[-1],'op':op,'segment':key[1]})
                elif op in ('memory.init','table.init'):
                    immediate=[x for x in n[1:] if isinstance(x,str)]
                    key=('data' if op=='memory.init' else 'elem',int(immediate[-1]))
                    if key in state:
                        raise Unproved('read before definite drop: '+repr(key)+' via '+repr(active))
            return state
        def func(i,state):
            if i in active: raise Unproved('recursive call')
            if i<0 or i>=len(funcs): raise Unproved('function index')
            active.append(i)
            try: return seq(funcs[i][1:],set(state))
            finally: active.pop()
        for i in roots:
            func(i,set(differing));checked.append(i)
        return {'status':'certified-no-segment-effect','roots':roots,'checkedRoots':checked,'events':events}
    except (Unproved, ValueError) as e:
        return {'status':'unproved','reason':str(e),'roots':roots,'checkedRoots':checked}


def main(source, measured, out):
    out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((source/'manifest.json').read_text());results=json.loads((measured/'results.json').read_text());cases=[]
    for row in results['rows']:
        if row['backend']!='migrate' or row['kind']!='observed': continue
        selected=[s for s in row.get('scenarios',[]) if s['status']=='restored' and s['entryMatches']
                  and s['comparison']['guestMemory'] and s['comparison']['tableTags'] and not s['comparison']['segments']]
        if not selected: continue
        c=manifest['cases'][row['id']];m=k.p.read(source/c['original']);extended,_=k.augment(m,True)
        for segment in c['observer']['segments']:
            kind,index=segment['kind'],segment['index']
            extended.append(k.p.expr(f'(func (export "__ctx_drop_{kind}_{index}") ({kind}.drop {index}))'))
        for index in c['tags']:
            extended.append(['export',f'"__ctx_func_{index}"',['func',str(index)]])
        dst=out/f'case-{c["id"]:02}.wasm';k.p.compile_wat(k.p.w.emit(extended),dst)
        signatures=[];types=k.p.section(m,'type');funcs=k.p.section(m,'func')
        for e in k.p.section(m,'export'):
            if e[2][0]!='func': continue
            f=funcs[int(e[2][1])];typ=types[int(next(x[1] for x in f[1:] if x[0]=='type'))][1]
            params=[t for x in typ[1:] if x[0]=='param' for t in x[1:]]
            signatures.append({'name':json.loads(e[1]),'params':params})
        scenarios=[]
        for s in selected:
            diffs=[(seg['kind'],seg['index']) for seg,a,b in zip(c['observer']['segments'],row['expectedState']['segments'],s['state']['segments']) if a!=b]
            scenarios.append({'stopAt':s['stopAt'],'differing':[list(x) for x in diffs],'certificate':certify(m,diffs)})
        cases.append({'case':c,'normalized':dst.name,'api':signatures,'finiteProfile':finite_profile(m),'scenarios':scenarios})
    shutil.copy2(Path(__file__),out/Path(__file__).name)
    shutil.copy2(Path(__file__).with_name('context-run.mjs'),out/'context-run.mjs')
    (out/'manifest.json').write_text(json.dumps({'source':str(source.resolve()),'measured':str(measured.resolve()),'cases':cases,
       'inputHashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'manifest.json',measured/'results.json')}},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    print(json.dumps({'cases':len(cases),'scenarios':sum(len(c['scenarios']) for c in cases),
                      'certified':sum(s['certificate']['status']=='certified-no-segment-effect' for c in cases for s in c['scenarios'])}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('measured',type=Path);a.add_argument('out',type=Path)
    v=a.parse_args();main(v.source,v.measured,v.out)
