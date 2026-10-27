import itertools
import json
from pathlib import Path
import sys
import time
import prototype as p

def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);d=3;hist={};examples={};start=time.perf_counter();nonterm=0
    for flat in itertools.product(range(d+2),repeat=2*d):
        r={'n':2,'d':d,'bound':d*(1<<d)+1,'edges':[flat[2*i:2*i+2] for i in range(d)]}
        values=[p.simulate(r,x)[0] for x in range(4)]
        if None in values:nonterm+=1;continue
        mask=sum(v<<i for i,v in enumerate(values));hist[mask]=hist.get(mask,0)+1;examples[mask]=r
    result={'d':d,'n':2,'networks':(d+2)**(2*d),'nonterminating_for_some_input':nonterm,'truth_histogram':hist,'examples':examples,'elapsed_ms':1000*(time.perf_counter()-start)}
    (out/'enumeration.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='examples'}))

if __name__=='__main__':main(sys.argv[1])
