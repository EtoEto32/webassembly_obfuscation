"""Separate optimization support from adaptive normalizer support."""
import split as s
import pathlib,sys,json,random
src=s.ROOT/sys.argv[1];out=s.ROOT/sys.argv[2];out.mkdir(parents=True,exist_ok=False)
rows=[];rng=random.Random(1818)
for row in json.loads((src/'records.json').read_text()):
    n,seed=row['n'],row['seed'];a=row['cut'][0]
    # Locate by cut ordinal saved by the generator, not by assumed numeric cut identity.
    cut=next(i for i in (1,2,3) if max(1,n*i//5)==a)
    stem=f'n{n}-s{seed}-cut{cut}'
    target=src/(stem+'.wasm');optimized=out/(stem+'.wasm')
    s.tool('wasm-opt',target,'--all-features','-O3','-o',optimized)
    base=s.read(src/f'n{n}-s{seed}.wasm');f=next(f for f in base[1:] if f[0]=='func')
    ops=s.chain(f[-1],s.nodes(f,'param')[0][1])
    xs=[0,1,-1,2147483647,-2147483648]+[rng.randrange(-2147483648,2147483648) for _ in range(100)]
    checks='\n'.join('(assert_return (invoke "run" (i32.const %d)) (i32.const %d))'%(x,s.value(ops,x)) for x in xs)
    wast=optimized.with_suffix('.wast');wast.write_text(s.tool('wasm-dis',optimized)+'\n'+checks,encoding='utf-8')
    s.tool('wasm-shell',wast)
    status='not_attempted';error=None
    try:
        s.recover(optimized,out/(stem+'-recovered.wasm'));status='recovered'
        rec=out/(stem+'-recovered.wasm');w=rec.with_suffix('.wast')
        w.write_text(s.tool('wasm-dis',rec)+'\n'+checks,encoding='utf-8');s.tool('wasm-shell',w)
    except ValueError as e:status='normalizer_profile_unsupported';error=str(e)
    rows.append(dict(target=stem,optimized_correct_inputs=len(xs),recovery_status=status,error=error,bytes=optimized.stat().st_size))
(out/'records.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
(out/'commands.json').write_text(json.dumps(s.CALLS,indent=2),encoding='utf-8')
print(json.dumps(dict(conditions=len(rows),statuses={k:sum(r['recovery_status']==k for r in rows) for k in set(r['recovery_status'] for r in rows)})))
