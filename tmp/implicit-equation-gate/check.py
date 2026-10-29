"""A mathematical gate, not a Wasm obfuscator or a blind recovery attack."""
from pathlib import Path
import json,random,hashlib

def mix(a,b,mask):
    return ((a+2*(a*a+a*b+b))&mask,(b+2*(a+b*b))&mask)

def invert(p,q,w):
    mask=(1<<w)-1; a=b=0
    for _ in range(w):
        a,b=(p-2*(a*a+a*b+b))&mask,(q-2*(a+b*b))&mask
    return a,b

rows=[]
for w in range(1,5):
    n=1<<w;mask=n-1;images=set();inverse_checks=0;root_checks=0
    for a in range(n):
        for b in range(n):
            image=mix(a,b,mask);images.add(image)
            assert invert(*image,w)==(a,b)
            inverse_checks+=1
    assert len(images)==n*n
    for x in range(n):
        for y in range(n):
            f=(x+y)&mask;g=(x*y)&mask
            for z in range(n):
                for t in range(n):
                    r=((z-f)&mask,(t-g)&mask)
                    assert (mix(*r,mask)==(0,0))==((z,t)==(f,g))
                    root_checks+=1
    rows.append({'width':w,'permutation_and_inverse_pairs':inverse_checks,'root_equivalence_quadruples':root_checks,'mismatches':0})
rng=random.Random(441721);inputs=[]
for _ in range(8192):
    a,b=rng.getrandbits(32),rng.getrandbits(32);inputs.append([a,b])
    assert invert(*mix(a,b,0xffffffff),32)==(a,b)
rotation_counterexamples=[]
for w in (4,8):
    n=1<<w;mask=n-1;seen={}
    for a in range(n):
        rotated=((a<<1)|(a>>(w-1)))&mask
        image=(a+2*rotated)&mask
        if image in seen:
            rotation_counterexamples.append({'width':w,'a':seen[image],'b':a,'same_image':image})
            break
        seen[image]=a
    assert rotation_counterexamples[-1]['width']==w
report={'seed':441721,'exhaustive':rows,'i32_random_inverse_pairs':len(inputs),'mismatches':0,
        'failed_extension':'a + 2*rotl(a,1) need not be a permutation; polynomial contraction proof does not apply.',
        'rotation_collisions':rotation_counterexamples,
        'scope':'Original mathematical prototype. Mixer and width are given. No source-free binary recovery, Wasm transformation, performance or security claim.',
        'input_sha256':hashlib.sha256(json.dumps(inputs).encode()).hexdigest()}
root=Path(__file__).resolve().parent
(root/'inputs.json').write_text(json.dumps(inputs))
(root/'results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
