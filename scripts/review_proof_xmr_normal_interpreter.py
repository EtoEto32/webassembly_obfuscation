"""Review algorithm-native interpreter as an RQ1 control; no Wasm execution."""
import json
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
texts={v:(P/f'xmr-{v}-f111-complete.wat.txt').read_text() for v in ['original','flattening']}
lines={v:t.splitlines() for v,t in texts.items()}
stack=[];tables=[]
for n,l in enumerate(lines['original'],1):
    s=l.strip()
    if s.startswith(('block ','loop ','if ')):stack.append(dict(line=n,construct=s))
    elif s=='end':stack.pop()
    elif s.startswith('br_table'):
        assert any(x['line']==2418 and x['construct']=='block $B26' for x in stack)
        tables.append(dict(line=n,branch=s))
assert len(tables)==70 and 'br_table' not in texts['flattening']
guard='\n'.join(lines['original'][2398:2421])
assert guard=='\n'.join(lines['flattening'][2398:2421])
assert all(x in guard for x in ['i32.load offset=2098672','i32.const 4','i32.ge_s','br_if $B26'])
assert all(x in '\n'.join(lines['original'][2760:2839]) for x in
           ['i32.load8_u offset=2','i32.load8_u offset=1','i32.load8_u','i32.mul','br_table'])
assert all(x in '\n'.join(lines['flattening'][2822:2973]) for x in
           ['i32.load8_u','i32.const 4','i32.lt_s','i32.const 1','i32.eq','i32.mul','br $B30'])
excerpts=[]
for variant,start,end in [('original',2760,2839),('flattening',2823,2973)]:
    path=P/f'xmr-{variant}-native-interpreter-reviewed.wat.txt'
    path.write_text('\n'.join(lines[variant][start-1:end])+'\n')
    excerpts.append(dict(variant=variant,lines=[start,end],path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as z:
    name='supp-materials/artifact/samples/xmr-wasm/src/crypto/variant4_random_math.h'
    t=z.read(name).decode();src=t.splitlines()
    path=P/'xmr-native-interpreter-source-reviewed.txt'
    path.write_text('\n'.join(src[24:164])+'\n')
    assert all(x in t for x in ['uint8_t opcode','uint8_t dst_index','uint8_t src_index',
        'switch (op->opcode)','*dst *= src','V4_EXEC_10(60)'])
def counts(v):
    c=Counter(l.strip().split()[0] for l in lines[v][2:] if l.strip())
    return {k:c[k] for k in ['block','loop','br','br_if','br_table','call','call_indirect']}
report=dict(function='$f111',reference_tables=tables,control_instruction_counts={v:counts(v) for v in texts},
    guard=dict(reference_and_flattened_lines=[2399,2421],condition='variant >= 4',
        consequence='All 70 reference br_table sites lie lexically in guarded block B26; recorded v0 inputs skip this path.'),
    first_operation_review=dict(reference_table_line=2821,opcode_load_line=2809,
        instruction_layout='opcode byte0, destination byte1, source byte2, constant word4',
        manually_corresponding_case='MUL: destination register multiplied by source register; table selection becomes comparisons/conditional branches.',
        scope='First selection and MUL payload reviewed; all 70 case bodies are not individually proven equivalent.'),
    source=dict(path=name,lines=[25,164],excerpt=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        interpretation='Distributed v4_random_math interpreter explicitly unrolls 70 operation selections; historical compiler identity not proven.'),
    excerpts=excerpts,
    interpretation='A normal mining algorithm already reads instruction records and interprets opcodes. Those features alone do not establish obfuscating virtualization. Removing br_table alone does not establish a state-update dispatcher.',
    limitations=['Manual correspondence plus lexical scope, not full semantic/dynamic reachability proof.',
                 'No causal runtime attribution, new hashing or helper execution.'])
(P/'xmr-normal-interpreter-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native interpreter control: 70 reference tables inside variant>=4; first MUL selection reviewed; no execution.')
