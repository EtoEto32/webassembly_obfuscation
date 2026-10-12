import ast
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'.tools/encoding-synthesis-python'))
import z3


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def bv(n):
    return '#x'+format(n & 0xffffffff,'08x')


def binary(operator,a,b):
    if operator in ('bvshl','bvlshr'):
        b=f'(bvand {b} {bv(31)})'
    return f'({operator} {a} {b})'


def expression(node,names):
    if isinstance(node,ast.Name):
        if node.id not in ('v0','v1'): raise ValueError(node.id)
        names.add(node.id)
        return node.id
    if isinstance(node,ast.Constant) and type(node.value) is int:
        return bv(node.value)
    if isinstance(node,ast.BinOp):
        ops={ast.Add:'bvadd',ast.Sub:'bvsub',ast.Mult:'bvmul',ast.BitXor:'bvxor',
             ast.BitAnd:'bvand',ast.BitOr:'bvor',ast.LShift:'bvshl',ast.RShift:'bvlshr'}
        return binary(ops[type(node.op)],expression(node.left,names),expression(node.right,names))
    if isinstance(node,ast.UnaryOp):
        operand=expression(node.operand,names)
        if isinstance(node.op,ast.UAdd): return operand
        return '('+{ast.USub:'bvneg',ast.Invert:'bvnot'}[type(node.op)]+' '+operand+')'
    raise ValueError(ast.dump(node))


def wat(node,names):
    if node[0]=='local.get' and len(node)==2:
        var='local_'+str(int(node[1]));names.add(var);return var
    if node[0]=='i32.const' and len(node)==2: return bv(int(node[1],0))
    ops={'i32.add':'bvadd','i32.sub':'bvsub','i32.mul':'bvmul','i32.xor':'bvxor',
         'i32.and':'bvand','i32.or':'bvor','i32.shl':'bvshl','i32.shr_u':'bvlshr'}
    if len(node)!=3 or node[0] not in ops: raise ValueError(node)
    return binary(ops[node[0]],wat(node[1],names),wat(node[2],names))


def query(a,b,names):
    return '(set-logic QF_BV)\n'+'\n'.join(f'(declare-fun {n} () (_ BitVec 32))' for n in sorted(names))+f'\n(assert (not (= {a} {b})))\n(check-sat)\n'


def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'artifacts/smt-local'
    out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((ROOT/'smt-protocol.json').read_text())
    results=json.loads((ROOT/'artifacts/results.json').read_text())
    manifest=json.loads((ROOT/'artifacts/rewritten/manifest.json').read_text())
    tasks=[]
    for i,row in enumerate(results['cases']):
        if row['status']!='returned': raise ValueError('unreturned case')
        names=set()
        left=expression(ast.parse(row['input'],mode='eval').body,names)
        right=expression(ast.parse(row['stdout'].strip(),mode='eval').body,names)
        tasks.append((f'cobra-{i}',query(left,right,names),'unsat',None))
    for i,row in enumerate(manifest['files']):
        for j,change in enumerate(row['changes']):
            names=set()
            left=wat(change['before'],names);right=wat(change['after'],names)
            tasks.append((f'rewrite-{i}-{j}',query(left,right,names),'unsat',None))
    tasks.append(('saved-mba',(ROOT.parent/'sha256-research-baseline/mba-add.smt2').read_text(),'unsat',None))
    tasks.append(('bad-carry-factor',query('(bvadd v0 v1)','(bvadd (bvxor v0 v1) (bvand v0 v1))',{'v0','v1'}),'sat','carry'))
    tasks.append(('bad-shift-semantics',query(binary('bvshl','v0',bv(32)),f'(bvshl v0 {bv(32)})',{'v0'}),'sat','shift'))
    rows=[]
    for name,text,expected,control in tasks:
        file=out/(name+'.smt2');file.write_text(text,encoding='utf-8')
        solver=z3.Solver();solver.set(timeout=protocol['timeout_ms_per_query'],max_memory=protocol['memory_mb'])
        solver.from_string(text)
        start=time.perf_counter();answer=solver.check();elapsed=time.perf_counter()-start
        row={'name':name,'query_sha256':digest(file),'expected':expected,'result':str(answer),'seconds':elapsed}
        if answer==z3.unknown: row['reason_unknown']=solver.reason_unknown()
        if answer==z3.sat:
            model=solver.model();row['model']={str(d):model[d].as_long() for d in model.decls()}
            if control:
                x=row['model'].get('v0',0);y=row['model'].get('v1',0)
                left=(x+y)&0xffffffff if control=='carry' else x
                right=((x^y)+(x&y))&0xffffffff if control=='carry' else 0
                row['python_replay']={'left':left,'right':right,'different':left!=right}
                if left==right: raise AssertionError('control model replay')
        row['statistics']=str(solver.statistics())
        rows.append(row)
        print(name,answer,flush=True)
    inputs=[ROOT/'smt-protocol.json',ROOT/'prove_local.py',ROOT/'artifacts/results.json',ROOT/'artifacts/rewritten/manifest.json',ROOT.parent/'sha256-research-baseline/mba-add.smt2']
    report={'z3':z3.get_full_version(),'python':platform.python_version(),'rows':rows,
            'all_expected':all(r['result']==r['expected'] for r in rows),
            'input_hashes':{str(p.relative_to(REPO)).replace('\\','/'):digest(p) for p in inputs}}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not report['all_expected']: sys.exit(2)


if __name__=='__main__': main()
