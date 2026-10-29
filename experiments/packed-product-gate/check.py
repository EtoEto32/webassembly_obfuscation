"""Exhaustive feasibility gate for a proposed packed-product rewrite."""
import hashlib,itertools,json,platform
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results.json'
if OUT.exists():raise SystemExit('Refuse overwrite results')
protocol=json.loads((ROOT/'protocol.json').read_text())

def packing(x,n,k,reverse=False):
    return sum(((x>>i)&1) << (k*(n-1-i if reverse else i)) for i in range(n))

def reference(x,y):
    # Popcount reference uses no packing/convolution implementation.
    return (x&y).bit_count()&1

rows=[]
for n in protocol['sizes']:
    safe=n.bit_length() # least k such that 2^k > n
    for k in range(1,safe+1):
        products={};extract_errors=0;first_extract=None;first_collision=None
        max_bits=0
        for x,y in itertools.product(range(1<<n),repeat=2):
            a=packing(x,n,k);b=packing(y,n,k,True);p=a*b
            expected=reference(x,y);actual=(p>>(k*(n-1)))&1
            max_bits=max(max_bits,p.bit_length())
            if actual!=expected:
                extract_errors+=1
                if first_extract is None:first_extract={'x':x,'y':y,'A':a,'B':b,'P':p,'expected':expected,'extracted':actual}
            if p not in products:products[p]={}
            if expected not in products[p]:products[p][expected]=[x,y]
            if len(products[p])==2 and first_collision is None:
                first_collision={'P':p,'inputs_for_zero':products[p][0],'inputs_for_one':products[p][1]}
        ambiguous=sum(len(v)==2 for v in products.values())
        if k==safe:assert extract_errors==0 and ambiguous==0
        if first_collision:
            u,v=first_collision['inputs_for_zero'],first_collision['inputs_for_one']
            # Independent Horner encoding checks the retained collision witness.
            def horner(x,reverse):
                bits=list(format(x,f'0{n}b'))
                if reverse:bits.reverse()
                acc=0
                for bit in bits:acc=acc*(1<<k)+int(bit)
                return acc
            assert horner(u[0],False)*horner(u[1],True)==horner(v[0],False)*horner(v[1],True)==first_collision['P']
            assert reference(*u)==0 and reference(*v)==1
        rows.append({'n':n,'k':k,'radix':1<<k,'cases':1<<(2*n),'max_product_bits':max_bits,'extraction_errors':extract_errors,'ambiguous_products':ambiguous,'distinct_products':len(products),'first_extraction_error':first_extract,'first_collision':first_collision,'carry_free_control':k==safe})

# Width-independent counterexample for k=1, embedded by zero padding.
extended=[]
for n in [4,8,16,32]:
    left=[1,9];right=[3,12]
    assert reference(*left)==1 and reference(*right)==0
    p=packing(left[0],n,1)*packing(left[1],n,1,True)
    q=packing(right[0],n,1)*packing(right[1],n,1,True)
    assert p==q==9*(1<<(n-4))
    extended.append({'n':n,'left':left,'right':right,'product':p,'outputs':[1,0]})

sample={'sample_id':'packed-gf2-inner-product-n4-k1','before':'((x & y).bit_count() & 1), x,y are 4-bit unsigned words','after':{'pack_x':'sum(bit(x,i) << i for i in 0..3)','pack_y':'sum(bit(y,i) << (3-i) for i in 0..3)','product':'pack_x * pack_y','decode':'(product >> 3) & 1'},'status':'generated candidate specification; incorrect on saved witnesses, not a completed transformation','witness':extended[0]}
(ROOT/'sample.json').write_text(json.dumps(sample,indent=2))
result={'python':platform.python_version(),'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows,'general_counterexample_checks':extended,'cases':sum(r['cases'] for r in rows),'decision':'reject general k=1 product-only candidate; no-carry fallback is known arithmetic packing'}
OUT.write_text(json.dumps(result,indent=2))
print(json.dumps({'rows':len(rows),'cases':result['cases'],'ambiguous_configurations':sum(r['ambiguous_products']>0 for r in rows),'control_cases':sum(r['cases'] for r in rows if r['carry_free_control']),'maximum_product_bits':max(r['max_product_bits'] for r in rows)}))
