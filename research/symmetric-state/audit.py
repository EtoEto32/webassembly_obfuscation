"""Independent post-attack comparisons, negative controls and state-fiber census."""
import collections, json, sys
from pathlib import Path
import probe as p

def main():
    d=Path(sys.argv[1]).resolve();m=json.loads((d/'manifest.json').read_text())
    checks=json.loads((d/'checks.json').read_text());verified=[]
    for a in m['artifacts']:
        assert p.sha(d/a['file'])==a['sha256']
    # Original is allowed here only AFTER the standalone attack produced output.
    for a in m['attacks']:
        assert a['status']=='recovered' and a['execution_queries']==0
        original=p.step_values(p.items(p.read(d/a['kernel']/'plain.wasm'),'func')[0])
        recovered=p.step_values(p.items(p.read(d/a['kernel']/('recovered-'+a['level']+'.wasm')),'func')[0])
        matches=any(all(p.canon(u-v)==0 for u,v in zip(original,order)) for order in (recovered,recovered[::-1]))
        assert matches
        verified.append({'kernel':a['kernel'],'level':a['level'],'updates_equal_mod_2_32_up_to_exchange':True})
    control=d/'negative-controls';control.mkdir();results=[]
    changes=[('non-equivariant-step','encode'),('changed-source-observer','encode'),
             ('exported-step','encode'),('changed-quotient-observer','attack')]
    for name,command in changes:
        src=d/'quadratic'/('quotient.wasm' if command=='attack' else 'plain.wasm')
        tree=p.read(src);fs=p.items(tree,'func')
        if name=='non-equivariant-step':fs[0][-1]=['i32.add',fs[0][-1],['i32.const','1']]
        elif name=='exported-step':tree.append(['export','"step"',['func','0']])
        else:fs[1][-1]=['local.get','0']
        bad=control/(name+'.wasm');p.write(bad,tree)
        try:
            (p.encode if command=='encode' else p.attack)(bad,control/(name+'-unexpected.wasm'))
            raise AssertionError('accepted '+name)
        except ValueError as e:results.append({'case':name,'status':'rejected','reason':str(e)})
    fibers=[]
    for bits in range(2,9):
        modulus=2**bits;counts=collections.Counter();witness={}
        for a in range(modulus):
            for b in range(modulus):counts[((a+b)%modulus,a*b%modulus)]+=1
        fibers.append({'bits':bits,'ordered_states':modulus**2,'image_size':len(counts),
                       'largest_fiber':max(counts.values()),'zero_fiber':counts[(0,0)],
                       'fibers_larger_than_two':sum(n>2 for n in counts.values())})
    # Exact zero-fiber construction at native width: y=-x, x divisible by 2^16.
    for k in range(2**16):
        a=k*2**16;b=(-a)&p.MASK
        assert (a+b)&p.MASK==0 and a*b&p.MASK==0
    assert len(checks['rows'])==36 and all(r['mismatches']==0 and r['unexpectedTraps']==0 for r in checks['rows'])
    report={'post_attack_source_comparisons':verified,'negative_controls':results,'small_width_fibers':fibers,
            'native_zero_fiber_constructed_distinct_ordered_states':2**16,
            'cases':sum(r['cases'] for r in checks['rows']),
            'note':'Snapshot collisions do not prevent public-code update recovery; no cryptographic secrecy claim.',
            'dependencies':{str(q.relative_to(p.ROOT)):p.sha(q) for q in [Path(p.__file__),Path(__file__),p.ROOT/'research/observation-synthesis/transform.py']}}
    p.save(d/'audit.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
