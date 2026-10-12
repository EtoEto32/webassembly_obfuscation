"""Review f113 dispatcher entry and first loop test only; no execution."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
b=(P/'xmr-original-f113-mechanism-review.wat.txt').read_text()
a=(P/'xmr-flattening-f113-mechanism-review.wat.txt').read_text()
for variant,text in [('original',b),('flattening',a)]:
    assert text.rstrip() in (P/f'xmr-{variant}.wat').read_text()
bl,al=b.splitlines(),a.splitlines()
# Reviewed straight-line initialization payload: exclude surrounding control flow.
old=[x.strip() for x in bl[167:406]]
new=[x.strip() for x in al[1035:1274]]
assert len(old)==len(new)==239
def alpha(lines):
    names={}
    def replace(m):
        name=m[0]
        if name=='$l4':return '$FRAME'
        return names.setdefault(name,f'$TMP{len(names)}')
    return [re.sub(r'\$l\d+',replace,x) for x in lines]
ob,na=alpha(old),alpha(new)
changes=[]
for i,(x,y) in enumerate(zip(ob,na)):
    if x==y:continue
    operand=r'(?<![A-Za-z0-9])(-?\d+)$'
    numsx=re.findall(operand,x);numsy=re.findall(operand,y)
    assert re.sub(operand,'#',x)==re.sub(operand,'#',y)
    assert len(numsx)==len(numsy)==1 and int(numsy[0])-int(numsx[0])==32
    changes.append(dict(reference_line=i+168,transformed_line=i+1036,
                        before=old[i],after=new[i]))
# This text match alone is not aliasing, trap or semantic equivalence proof.
assert 'i32.const 295792562' in a and 'i32.store offset=16' in a
assert 'i32.load offset=16' in a and 'i32.store offset=12' in a
assert 'br $L0' in a and 'br_table' not in a
assert 'i32.const -1569009996' in '\n'.join(al[1274:1283])
assert all(x in '\n'.join(al[1284:1320]) for x in
           ['i32.load offset=352','i32.const 45','i32.lt_s',
            'i32.const 2118300141','i32.const -425016634','select','br $B1'])
stack=[];contexts=[]
for n,l in enumerate((P/'xmr-original-f111-complete.wat.txt').read_text().splitlines(),1):
    s=l.strip()
    if s.startswith(('block ','loop ','if ')):stack.append(dict(line=n,construct=s))
    elif s=='end':stack.pop()
    elif s=='call $f113':contexts.append(dict(line=n,enclosing_constructs=stack.copy()))
assert len(contexts)==1 and not any(r['construct'].startswith('loop ') for r in contexts[0]['enclosing_constructs'])
report=dict(function='$f113',scope='Dispatcher presence, initialization payload, first condition only; remainder not reviewed.',
    reference_sha256=hashlib.sha256(b.encode()).hexdigest(),transformed_sha256=hashlib.sha256(a.encode()).hexdigest(),
    state_offset=16,state_pointer_offset=12,
    reviewed_transitions=[dict(state=295792562,operation='Initialize scratch data',next=-1569009996),
        dict(state=-1569009996,operation='Signed scratch word < 45',next_if_true=2118300141,next_if_false=-425016634)],
    initialization_payload=dict(reference_lines=[168,406],transformed_lines=[1036,1274],
        instruction_text_lines=239,alpha_renamed_matching_except_address_changes=True,
        changed_numeric_operands=changes,
        interpretation='Reviewed frame size increases 576 to 608; recorded scratch coordinates increase by 32. Opcode/local dataflow text agrees for this payload, not whole-function equivalence.'),
    reference_call_contexts=contexts,
    limitations=['All state meanings, complete graph and source function identity remain unconfirmed.',
                 'Single caller site is lexically in a block, not a structured loop; no dynamic path/frequency claim.',
                 'No hash execution, full alias/trap analysis or attribution of runtime difference.'])
(P/'xmr-f113-dispatch-entry-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'f113 entry/first condition reviewed; 239 payload lines, {len(changes)} coordinate changes; rest unreviewed.')
