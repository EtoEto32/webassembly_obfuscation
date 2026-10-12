"""Review a bounded flattening fragment in the unexecuted hash candidate."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
names=['410426ab2346','b11438f04601']
texts=[(OUT/f'cryptonight-{s}-f10.wat.txt').read_text() for s in names]
lines=[t.splitlines() for t in texts]
flat=lines[1]
# Resolve labelled ends by lexical nesting, rather than nearby text alone.
nesting=[];bounds={}
for number,line in enumerate(flat,1):
    instruction=line.strip()
    opening=re.match(r'(block|loop|if)(?:\s+(\$\S+))?',instruction)
    if opening:
        nesting.append((opening.group(2),number))
    elif instruction=='end':
        label,start=nesting.pop()
        if label:bounds[label]=(start,number)
assert not nesting
for label,expected in {'$L0':(206,1617),'$B1':(216,1615),
                        '$B11':(226,1138),'$B12':(227,969),'$B13':(228,933)}.items():
    assert bounds[label]==expected,(label,bounds.get(label))
assert flat[205].strip()=='loop $L0'
assert [s.strip() for s in flat[206:210]]==['local.get $l5','i32.load offset=12','local.set $l51','i32.const -2080045202']
assert 'i32.const 1819809018' in '\n'.join(flat[185:205])
# Exact tail: the common branch out of B1 returns to the dispatcher loop.
assert [s.strip() for s in flat[-4:]]==['end','br $L0','end','unreachable)']
condition='\n'.join(s.strip() for s in flat[933:970])
assert 'i32.const 524288' in condition and 'i32.lt_u' in condition
assert 'i32.const -1434013805' in condition and 'i32.const -739629170' in condition
assert 'select\nlocal.set $l249\nlocal.get $l5\ni32.load offset=8\nlocal.set $l250\nlocal.get $l250\nlocal.get $l249\ni32.store\nbr $B1' in condition
increment='\n'.join(s.strip() for s in flat[1138:1159])
assert 'i32.const 1' in increment and 'i32.add' in increment
assert 'i32.store offset=2097596' in increment and 'i32.const -1465685751' in increment
assert increment.endswith('br $B1')
payload_tail='\n'.join(s.strip() for s in flat[1126:1138])
assert 'call $f14' in payload_tail and 'i32.const -1408174823' in payload_tail and 'br $B1' in payload_tail
dispatch='\n'.join(s.strip() for s in flat[206:400])
for value,label in [(-1465685751,'$B13'),(-1434013805,'$B12'),(-1408174823,'$B11')]:
    pattern=rf'i32.const {value}\nlocal.set (\$l\d+)\nlocal.get \$l51\nlocal.get \1\ni32.eq\nlocal.set (\$l\d+)\nlocal.get \2\nbr_if {re.escape(label)}'
    assert re.search(pattern,dispatch),(value,label)

fragments=[];norms=[];types=[]
for i,(text,ls) in enumerate(zip(texts,lines)):
    a=next(j for j,s in enumerate(ls) if s.strip()=='call $f24')
    z=next(j for j,s in enumerate(ls[a:],a) if s.strip()=='call $f14')
    start=a-50;segment=[s.strip() for s in ls[start:z+1]]
    mapping={};normalized=[];offsets={}
    for s in segment:
        s=re.sub(r'\$l\d+',lambda m:mapping.setdefault(m[0],f'$N{len(mapping)}'),s)
        if i==0:
            def adjust(m):
                value=int(m[1]);offsets[value]=value+16
                return 'offset='+str(value+16)
            s=re.sub(r'offset=(20975\d+)',adjust,s)
        normalized.append(s)
    decl=dict(re.findall(r'\(local (\$l\d+) (i32|i64|f32|f64)\)',ls[1]))
    types.append({mapping[k]:v for k,v in decl.items() if k in mapping})
    norms.append(normalized)
    fragments.append(dict(file=f'cryptonight-{names[i]}-f10.wat.txt',sha256=hashlib.sha256(text.encode()).hexdigest(),
        reviewed_fragment_lines=[start+1,z+1],fragment_instruction_text_lines=len(segment),
        direct_calls=re.findall(r'\bcall (\$[^\s()]+)','\n'.join(segment)),
        reference_stack_offsets_to_variant=offsets if i==0 else None))
assert norms[0]==norms[1] and types[0]==types[1]
assert len(norms[0])==157
# Symbolically trace only the straight-line counter/control fragments. No Wasm
# instance or cryptographic operation is executed by this analysis.
def trace_fragment(which,start,end):
    stack=[];locals_={'$l5':('stack_base',)};events=[]
    for raw in lines[which][start-1:end]:
        ins=raw.strip();parts=ins.split();op=parts[0]
        if op=='local.get':stack.append(locals_[parts[1]])
        elif op=='local.set':locals_[parts[1]]=stack.pop()
        elif op=='i32.const':stack.append(int(parts[1]))
        elif op in ('i32.load','i32.store'):
            offset=int(parts[1].split('=')[1]) if len(parts)>1 else 0
            if which==0 and offset>=2097500:offset+=16
            if op=='i32.load':stack.append(('load',stack.pop(),offset))
            else:
                value=stack.pop();address=stack.pop()
                events.append(('store',address,offset,value))
        elif op in ('i32.lt_u','i32.and','i32.add'):
            right=stack.pop();left=stack.pop();stack.append((op,left,right))
        elif op=='i32.eqz':stack.append((op,stack.pop()))
        elif op=='select':
            condition=stack.pop();false_value=stack.pop();true_value=stack.pop()
            stack.append(('select',condition,true_value,false_value))
        elif op=='br_if':events.append(('br_if',parts[1],stack.pop()))
        elif op=='br':events.append(('br',parts[1]))
        else:raise AssertionError(('unsupported fragment instruction',ins))
    assert not stack
    return events
base=('stack_base',);counter=('load',base,2097596)
predicate=('i32.and',('i32.lt_u',counter,524288),1)
state_pointer=('load',base,8)
counter_reviews={
    'reference_initialization':trace_fragment(0,558,562),
    'variant_initialization':trace_fragment(1,919,932),
    'reference_condition':trace_fragment(0,565,582),
    'variant_condition':trace_fragment(1,934,968),
    'reference_increment':trace_fragment(0,742,754),
    'variant_increment':trace_fragment(1,1139,1159)}
assert counter_reviews['reference_initialization']==[('store',base,2097596,0)]
assert counter_reviews['variant_initialization']==[('store',base,2097596,0),
    ('store',state_pointer,0,-1465685751),('br','$B1')]
assert counter_reviews['reference_condition']==[('br_if','$B6',('i32.eqz',predicate))]
assert counter_reviews['variant_condition']==[('store',state_pointer,0,
    ('select',predicate,-1434013805,-739629170)),('br','$B1')]
increment_event=('store',base,2097596,('i32.add',counter,1))
assert counter_reviews['reference_increment']==[increment_event,('br','$L7')]
assert counter_reviews['variant_increment']==[increment_event,
    ('store',state_pointer,0,-1465685751),('br','$B1')]
report=dict(date='2026-10-08',function='$f10 (partial-ABI hash candidate)',fragments=fragments,
    counter_fragment_symbolic_events=counter_reviews,
    counter_review_scope='Straight-line fragments only: common zero initialization, unsigned bound and increment by one; variant writes dispatcher states instead of the reference loop branches. Memory/callee side effects between fragments and whole-loop equivalence remain unverified.',
    mechanism=dict(state_slot='stack base + 12',state_pointer_slot='stack base + 8',initial_state=1819809018,
        common_dispatch_loop='$L0',common_case_exit='$B1',
        lexical_block_bounds={k:bounds[k] for k in ['$L0','$B1','$B11','$B12','$B13']},
        reviewed_subgraph=[dict(state=-1465685751,role='unsigned counter < 524288',true_state=-1434013805,false_state=-739629170),
            dict(state=-1434013805,role='core fragment with six direct calls',next_state=-1408174823),
            dict(state=-1408174823,role='counter increment by one',next_state=-1465685751)]),
    fragment_match='157 instruction-text lines match under consistent local renaming and observed +16 stack-slot displacement; referenced local types and direct callee identifiers match.',
    implication='State dispatch replaces part of a high-iteration loop inside the hash candidate, rather than merely its outer main wrapper. Actual execution and timing effect remain unmeasured.',
    limitations=['Only a bounded loop subgraph and payload fragment were reviewed; other dispatcher states and full-body equivalence unverified.',
        'Full cryptographic callee semantics and historical source/binary correspondence are not proven by unchanged call identifiers.',
        'Static counter bound does not establish dynamic execution count, coverage, successful hash output or causal overhead.',
        'The candidate is not part of the already measured 13-module runtime comparison.'],executed_hashes=0)
(OUT/'cryptonight-core-flattening-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Reviewed dispatcher subgraph and matched 157 core-fragment lines; no execution.')
