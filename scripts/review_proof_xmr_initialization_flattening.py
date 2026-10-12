"""Record manual static review of f83; do not execute Wasm or hashing."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
before = (OUT / 'xmr-original-f83-mechanism-review.wat.txt').read_text()
after = (OUT / 'xmr-flattening-f83-mechanism-review.wat.txt').read_text()
for variant, excerpt in [('original', before), ('flattening', after)]:
    assert excerpt.rstrip() in (OUT / f'xmr-{variant}.wat').read_text()
    assert 'br_table' not in excerpt
    assert re.findall(r'\bcall (\$\w+)', excerpt) == ['$f218', '$f84', '$f178', '$f85']
assert 'loop ' not in before
assert after.index('call $f218') < after.index('loop $L0')
assert all(x in after for x in ['i32.store offset=16', 'i32.load offset=16',
                               'i32.store offset=12', 'br $L0'])
transitions = [
    dict(state=-759120739, operation='Check allocated context == 0',
         next_if_true=450301759, next_if_false=-1660447243),
    dict(state=450301759, operation='Set result to null', next=422192835),
    dict(state=-1660447243,
         operation='Call f84 then f178; clear first context field; call f85(context,2,0); set context result',
         next=422192835),
    dict(state=422192835, operation='Restore entry stack pointer and return result')]
for row in transitions:
    assert f"i32.const {row['state']}\n" in after
contexts = []
stack = []
core = (OUT / 'xmr-original-f111-complete.wat.txt').read_text()
for number, line in enumerate(core.splitlines(), 1):
    token = line.strip()
    if token.startswith(('block ', 'loop ', 'if ')):
        stack.append(dict(line=number, construct=token))
    elif token == 'end':
        stack.pop()
    elif token == 'call $f83':
        contexts.append(dict(line=number, enclosing_constructs=stack.copy()))
assert len(contexts) == 1 and not contexts[0]['enclosing_constructs']
with zipfile.ZipFile(ROOT / 'data/archives/proof-of-theft.zip') as archive:
    name = 'supp-materials/artifact/samples/xmr-wasm/src/crypto/oaes_lib.c'
    text = archive.read(name).decode()
    match = re.search(r'\boaes_alloc\s*\([^;{}]*\)\s*\{', text)
    assert match
    start, end, depth = match.start(), match.end(), 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    source = text[start:end]
    path = OUT / 'xmr-oaes-alloc-source-reviewed.txt'
    path.write_text(source + '\n')
    assert all(x in source for x in ['calloc(', 'srand( oaes_get_seed()', '_ctx->key = NULL', 'oaes_set_option'])
report = dict(
    function='$f83', mechanism='State-dispatched context initialization and null-result handling after allocation.',
    reference_excerpt_sha256=hashlib.sha256(before.encode()).hexdigest(),
    flattened_excerpt_sha256=hashlib.sha256(after.encode()).hexdigest(),
    state_offset=16, state_pointer_offset=12, result_offset=28,
    allocation_before_dispatcher=True, manually_reviewed_transitions=transitions,
    source_correspondence=dict(path=name, line=text[:start].count('\n') + 1,
        excerpt=str(path), excerpt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        interpretation='Allocation/null guard, seed setup, key clearing, options and context return correspond to the non-ISAAC path of distributed oaes_alloc. No debug-symbol or historical build identity proof.'),
    reference_call_contexts=contexts,
    interpretation='The sole lexical f111 call is before its structured loops, not a demonstrated per-iteration hot-loop call. Each hash invocation may still execute initialization; no dynamic count measured.',
    limitations=['Manual static graph, not machine-checked equivalence or dynamic coverage.',
                 'Callees, conditional compilation and historical source-to-binary identity are not fully mapped.',
                 'No hash execution or causal allocation of measured runtime overhead.'])
(OUT / 'xmr-initialization-flattening-review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Initialization: four reviewed states; allocation before dispatcher; caller outside structured loops; no execution.')
