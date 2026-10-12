"""Independent exhaustive check of carry-settling lemma, small widths only."""
import json
from pathlib import Path
results=[]
for w in range(1,6):
    size=1<<w; mask=size-1; count=0
    for a in range(size):
        for b in range(size):
            for initial in range(size):
                c=initial
                for step in range(w):
                    s=a^b^c
                    c=(((a&b)|((a^b)&c))<<1)&mask
                assert s==((a+b)&mask),(w,a,b,initial,s)
                count+=1
    results.append({'width':w,'triples':count,'mismatches':0})
Path(__file__).with_name('carry-check.json').write_text(json.dumps(results,indent=2))
print(results)
