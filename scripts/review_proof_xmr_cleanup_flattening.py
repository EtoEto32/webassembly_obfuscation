"""Record manually reviewed f86 dispatcher and source-level cleanup correspondence."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
before = (OUT/'xmr-original-f86-mechanism-review.wat.txt').read_text()
after = (OUT/'xmr-flattening-f86-mechanism-review.wat.txt').read_text()
for variant, excerpt in [('original',before),('flattening',after)]:
    assert excerpt.rstrip() in (OUT/f'xmr-{variant}.wat').read_text()
    assert 'br_table' not in excerpt
    assert re.findall(r'\bcall (\$\w+)',excerpt) == ['$f78','$f217']
assert 'loop ' not in before
assert all(fragment in after for fragment in [
    'i32.store offset=12','i32.load offset=12',
    'i32.store offset=8','i32.load offset=8','loop $L0','br $L0'])
transitions = [
    dict(state=1290003362, operation='Check argument pointer p0 == 0',
         next_if_true=-1759823793,next_if_false=704486594),
    dict(state=-1759823793,operation='Set result to 2',next=593021969),
    dict(state=704486594,operation='Check context pointer *p0 == 0',
         next_if_true=-316282812,next_if_false=833403),
    dict(state=-316282812,operation='Set result to 0',next=593021969),
    dict(state=833403,operation='Check first context field **p0 != 0',
         next_if_true=1912538748,next_if_false=-2066247667),
    dict(state=1912538748,operation='Call f78 with *p0',next=-2066247667),
    dict(state=-2066247667,operation='Call f217 with *p0; clear *p0; set result 0',next=593021969),
    dict(state=593021969,operation='Restore entry stack pointer; return result')]
for row in transitions:
    assert f"i32.const {row['state']}\n" in after
contexts = []
stack = []
core = (OUT/'xmr-original-f111-complete.wat.txt').read_text()
for number,line in enumerate(core.splitlines(),1):
    token=line.strip()
    if token.startswith(('block ','loop ','if ')):
        stack.append(dict(line=number,construct=token))
    elif token == 'end':
        stack.pop()
    elif token == 'call $f86':
        contexts.append(dict(line=number,enclosing_constructs=stack.copy()))
assert len(contexts)==1 and not contexts[0]['enclosing_constructs']
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as archive:
    name='supp-materials/artifact/samples/xmr-wasm/src/crypto/oaes_lib.c'
    text=archive.read(name).decode()
    match=re.search(r'\boaes_free\s*\([^;{}]*\)\s*\{',text)
    assert match
    start,end,depth=match.start(),match.end(),1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    source=text[start:end]
    path=OUT/'xmr-oaes-free-source-reviewed.txt'
    path.write_text(source+'\n')
    assert 'oaes_key_destroy' in source and 'free( *_ctx )' in source and '*_ctx = NULL' in source
report=dict(function='$f86',
    mechanism='State-dispatched pointer validation, optional field cleanup, context release, and result return.',
    reference_excerpt_sha256=hashlib.sha256(before.encode()).hexdigest(),
    flattened_excerpt_sha256=hashlib.sha256(after.encode()).hexdigest(),
    state_offset=12,state_pointer_offset=8,result_offset=28,
    manually_reviewed_transitions=transitions,
    source_correspondence=dict(path=name,line=text[:start].count('\n')+1,
        excerpt=str(path),excerpt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        interpretation='Null guards, optional key cleanup, context free/clear and return codes correspond to distributed oaes_free source. No debug-symbol or historical build identity proof.'),
    reference_call_contexts=contexts,
    interpretation='The sole lexical f111 call occurs after its structured loops; this helper is not a demonstrated per-iteration hot-loop operation.',
    limitations=['Graph records manual static review, not dynamic execution or complete machine-checked equivalence.',
                 'Callees/data/conditional compilation and historical source-to-binary identity remain incompletely mapped.',
                 'No new hashing, dynamic frequency measurement, or causal allocation of runtime overhead.'])
(OUT/'xmr-cleanup-flattening-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Cleanup dispatcher reviewed: eight states, same call sequence, one f111 call outside structured loops; no execution.')
