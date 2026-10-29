"""Record static, location-linked observations; never execute collected Wasm."""
import collections
import hashlib
import json
from pathlib import Path
from measure_rq_validation import functions

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/mining-methods'


def main():
    selection = json.loads((OUT/'mechanism-selection.json').read_text(encoding='utf-8'))
    inputs = {r['stratum']: r for r in selection}
    cache = {}
    fs = {}
    for method, r in inputs.items():
        sha = r['sha256']
        cache[method] = json.loads((ROOT/'data/analysis-v2'/f'{sha}.json').read_text(encoding='utf-8'))
        obj = Path(cache[method]['object'])
        if not obj.is_absolute(): obj = ROOT/obj
        assert hashlib.sha256(obj.read_bytes()).hexdigest() == sha
        fs[method] = functions(sha)

    def excerpt(method, fn, start, end):
        ops = fs[method][fn]['ops']
        found = [o for o in ops if int(start,16) <= int(o['offset'],16) <= int(end,16)]
        assert found[0]['offset']==start and found[-1]['offset']==end
        return dict(method=method,sha256=inputs[method]['sha256'],function_index=fn,
                    file=f"results/cases/{inputs[method]['sha256']}/disassembly.txt",ops=found)

    def expect(e, offset, op, args):
        actual = next(o for o in e['ops'] if o['offset']==offset)
        assert (actual['op'],actual['args'])==(op,args),actual

    def branches(method, fn):
        stack=[dict(op='function',offset=None)]; result=[]
        for o in fs[method][fn]['ops']:
            if o['op'] in ('block','loop','if','try'): stack.append(o)
            elif o['op']=='end': stack.pop()
            elif o['op'] in ('br','br_if'):
                result.append(dict(source=o, target=stack[-1-int(o['args'])]))
        return result

    flat=excerpt('tigress/flatten',33,'009b13','009b43')
    expect(flat,'009b13','i32.const','5')
    expect(flat,'009b1b','i32.store','2 32')
    expect(flat,'009b22','i32.load','2 32')
    expect(flat,'009b43','br_table','5 0 6 7 7 3 2 7 7 1 4 7')
    flat_writes=[o for o in fs['tigress/flatten'][33]['ops'] if o['op']=='i32.store' and o['args']=='2 32']
    flat_back=[b for b in branches('tigress/flatten',33) if b['target']['offset']=='009b1e']
    assert len(flat_writes)>1 and flat_back

    vm=excerpt('tigress/virtualize',56,'040591','04070b')
    expect(vm,'040591','i32.const','168944')
    expect(vm,'04059b','i32.store','2 24')
    expect(vm,'0405a2','i32.load','2 24')
    expect(vm,'0405a9','i32.load8_u','0 0')
    expect(vm,'0406fc','i32.const','1')
    expect(vm,'040704','i32.add','')
    expect(vm,'04070b','i32.store','2 24')
    vm_back=[b for b in branches('tigress/virtualize',56) if b['target']['offset']=='04059e']
    assert vm_back

    original=excerpt('unobfuscated',23,'004be1','004c07')
    substitute=excerpt('llvm/subobf',23,'006ba8','006c1a')
    expect(original,'004bf0','i32.shl','')
    expect(original,'004c07','call','24')
    expect(substitute,'006c1a','call','24')
    expected=[('006bb7','i32.xor'),('006bc2','i32.and'),('006bcd','i32.or'),
              ('006bd8','i32.xor'),('006bdf','i32.mul'),('006bea','i32.and'),
              ('006bf5','i32.or'),('006bfc','i32.mul'),('006c03','i32.add')]
    for offset, op in expected: expect(substitute,offset,op,'')

    indirect=excerpt('tigress/antialiasanalysis',88,'052dad','052df7')
    expect(indirect,'052de7','i32.load','2 0')
    expect(indirect,'052df7','call_indirect','0 (type 3)')
    observations=[]
    for method, fn in [('unobfuscated',53),('tigress/flatten',33),
                       ('tigress/virtualize',56),('tigress/antialiasanalysis',88)]:
        # Save export metadata verbatim so reviewers can check the correspondence.
        observations.append(dict(method=method,function_index=fn,header=fs[method][fn]['header'],
            exports=cache[method]['exports'],
            opcode_counts=dict(collections.Counter(o['op'] for o in fs[method][fn]['ops'] if o['op']!='local'))))
    report=dict(
        scope='purpose-selected cn-0 mining-program cases; static interpretation, not whole-program equivalence or prevalence',
        selected_inputs=selection,
        export_correspondences=observations,
        claims=[
          dict(id='M1',method='tigress/flatten',status='state dispatcher confirmed locally',
               explanation='State 5 is stored at frame+32, reloaded for dispatch, and rewritten by handlers; branches return to the dispatch loop.',
               evidence=[flat],state_writes=flat_writes,back_edges=flat_back),
          dict(id='M2',method='tigress/virtualize',status='bytecode interpreter structure confirmed locally',
               explanation='A pointer initialized to 168944 is held at frame+24. A byte read through it selects a dispatcher after subtracting 16. A handler increments this pointer; branches return to the fetch loop. Full handler semantics and bytecode equivalence are not established.',
               evidence=[vm],dispatch_targets_including_default=len(next(o for o in vm['ops'] if o['op']=='br_table')['args'].split()),back_edges=vm_back),
          dict(id='M3',method='llvm/subobf',status='local arithmetic substitution confirmed',
               explanation='The value loaded from frame+8 is x. Original x<<3 and the replacement are passed in the corresponding argument position to call 24; other surrounding argument loads correspond.',
               expression='(x & ~8)*(~x & 8) + (x | 8)*(x & 8)',
               proof='All operations are 32-bit modular. Set u=x&~8, v=x&8, so x=u+v, v is 0 or 8, ~x&8=8-v, x|8=u+8. Then u*(8-v)+(u+8)*v=8*(u+v)=8*x=x<<3 modulo 2^32.',
               evidence=[original,substitute]),
          dict(id='M4',method='tigress/antialiasanalysis',status='memory-derived indirect call confirmed; callee equivalence not recovered',
               explanation='A comparison of loaded values selects 1436 or 8, added to 66688; the loaded table index is consumed by call_indirect. This is not a proof that every transformed call resolves to its original target.',evidence=[indirect])],
        unreviewed_mechanisms=['tigress/encodearithmetic','llvm/constenc'],
        review='Agent-assisted static inspection; independent human review remains required.',
        reproduction='python scripts/review_mining_mechanisms.py')
    (OUT/'mechanism-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(status='saved',claims=len(report['claims']),
                         flat_state_writes=len(flat_writes),flat_back_edges=len(flat_back),vm_back_edges=len(vm_back))))


if __name__=='__main__': main()
