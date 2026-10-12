"""Record reviewed f82 state graph from stored text, without Wasm execution."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
before = (OUT/'xmr-original-f82-mechanism-review.wat.txt').read_text()
after = (OUT/'xmr-flattening-f82-mechanism-review.wat.txt').read_text()
for variant, excerpt in [('original', before), ('flattening', after)]:
    assert excerpt.rstrip() in (OUT/f'xmr-{variant}.wat').read_text()
    assert 'br_table' not in excerpt
    assert re.findall(r'\bcall (\$\w+)', excerpt) == ['$f78','$f218','$f218','$f78','$f131','$f79','$f78']
assert 'loop ' not in before
# Rows are manual graph interpretation, not inferred obfuscation labels or execution.
rows = [
 (490629031,278,'context == null',211761890,-1975004456),
 (211761890,314,'result = 2',525789297),
 (-1975004456,329,'data == null',2003193629,-1836016991),
 (2003193629,365,'result = 3',525789297),
 (-1836016991,380,'copy length to scratch',-513924855),
 (-513924855,396,'length < 24 (signed)',695785137,129315292),
 (129315292,432,'length < 32 (signed)',1232620826,-448132808),
 (-448132808,468,'length == 32',-1769775337,-467972172),
 (1232620826,504,'length == 24',-1769775337,-467972172),
 (695785137,540,'length == 16',-1769775337,-467972172),
 (-1769775337,576,'continue after accepted length',-1158786421),
 (-467972172,586,'result = 4',525789297),
 (-1158786421,601,'existing key != null',143145029,-661205410),
 (143145029,640,'call f78 to release existing key',-661205410),
 (-661205410,656,'allocate key; key == null',-1737782779,1514030254),
 (-1737782779,709,'result = 8',525789297),
 (1514030254,724,'store length; allocate data; data == null',147393814,-1172841419),
 (147393814,796,'call f78; result = 8',525789297),
 (-1172841419,817,'copy data with f131; prior rc != 0; set scratch boolean true',614648350,-559442782),
 (-559442782,868,'call f79; scratch boolean = return != 0',614648350),
 (614648350,903,'copy boolean to rc; rc != 0',1386834935,1599361479),
 (1386834935,935,'call f78; result = rc',525789297),
 (1599361479,957,'result = 0',525789297),
 (525789297,972,'restore entry stack pointer; return result')]
transitions = []
for state, line, operation, *targets in rows:
    assert f'i32.const {state}\n' in after
    row = dict(state=state,body_line=line,operation=operation)
    if len(targets)==2:row.update(next_if_true=targets[0], next_if_false=targets[1])
    elif targets:row['next']=targets[0]
    transitions.append(row)
states = {r['state'] for r in transitions}
assert len(states)==24
assert all(t in states for r in rows for t in r[3:])
stack, contexts = [], []
for n,l in enumerate((OUT/'xmr-original-f111-complete.wat.txt').read_text().splitlines(),1):
    t=l.strip()
    if t.startswith(('block ','loop ','if ')):stack.append(dict(line=n,construct=t))
    elif t=='end':stack.pop()
    elif t=='call $f82':contexts.append(dict(line=n,enclosing_constructs=stack.copy()))
assert len(contexts)==2 and all(not r['enclosing_constructs'] for r in contexts)
with zipfile.ZipFile(ROOT/'data/archives/proof-of-theft.zip') as z:
    name='supp-materials/artifact/samples/xmr-wasm/src/crypto/oaes_lib.c'
    source=z.read(name).decode()
    m=re.search(r'\boaes_key_import_data\s*\([^;{}]*\)\s*\{',source)
    assert m
    end, depth=m.end(),1
    while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
    excerpt=source[m.start():end]
    path=OUT/'xmr-oaes-key-import-source-reviewed.txt';path.write_text(excerpt+'\n')
report=dict(function='$f82',state_offset=8,state_pointer_offset=4,result_offset=44,
    manually_reviewed_transitions=transitions,reference_call_contexts=contexts,
    excerpt_sha256=dict(original=hashlib.sha256(before.encode()).hexdigest(),flattening=hashlib.sha256(after.encode()).hexdigest()),
    mechanism='24-state dispatcher replaces structured guards, key allocation/copy/expansion and return handling; unchanged lexical call sequence.',
    source_correspondence=dict(path=name,line=source[:m.start()].count('\n')+1,
        excerpt=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        interpretation='Guards, lengths 16/24/32, allocation, copy, booleanized expansion status and cleanup correspond to distributed oaes_key_import_data; historical binary identity not proven.'),
    interpretation='Two lexical caller sites outside f111 structured loops; not per-iteration main-loop calls. Calls may occur each hash invocation; dynamic counts remain unmeasured.',
    limitations=['Manual static graph is not machine-checked equivalence or complete dynamic path coverage.',
                 'Callee bodies and historical compiler/source mapping incompletely reviewed.',
                 'No hashing, helper execution or causal allocation of runtime overhead.'])
(OUT/'xmr-key-import-flattening-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Key import: 24 reviewed states; two caller sites outside structured loops; no execution.')
