"""Early exact automata checks before the Wasm backend; not a full evaluation."""
import argparse
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import time
import model as m


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    cases={'suffix010':m.pattern([0,1,0]),'contains0110':m.pattern([0,1,1,0],True),
           'mod4':m.DFA([[(q+1)%4,(q+2)%4] for q in range(4)],1)}
    records=[];models={};guard=m.universal(3)
    ug,ur=m.determinize(guard);assert m.minimize(ug).n==1 and m.minimize(ug).final==1
    for name,d in cases.items():
        base=m.trim(m.lift(d,guard))
        for mode in ['lift','random','overlap']:
            n=base
            report={'rounds':0,'ms':0}
            if mode!='lift':n,report=m.choose_merges(d,n,12,20261018,mode)
            cert=m.certificate(d,n);assert cert['valid'];attacks=[]
            for attack in ['subset','bisimulation','reverse']:
                t=time.perf_counter();source=m.bisimulation(n) if attack=='bisimulation' else m.reverse(n) if attack=='reverse' else n
                recovered,ar=m.determinize(source)
                if recovered is not None:
                    recovered=m.minimize(recovered)
                    if attack=='reverse':
                        recovered,second=m.determinize(m.reverse(m.from_dfa(recovered)))
                        assert recovered is not None;ar['second_states']=second['states'];recovered=m.minimize(recovered)
                    equal,pairs=m.equivalent(d,recovered);assert equal
                    ar.update(minimal_states=recovered.n,equivalent=equal,check_pairs=pairs)
                ar.update(attack=attack,total_ms=(time.perf_counter()-t)*1000,reduced_nfa_states=source.n);attacks.append(ar)
            models[name+'.'+mode]=dict(dfa=asdict(d),nfa=asdict(n))
            rec=dict(name=name,mode=mode,guard_states=guard.n,nfa_states=n.n,certificate=cert,generation=report,attacks=attacks)
            records.append(rec);print(json.dumps({k:v for k,v in rec.items() if k not in ('certificate','generation')}),flush=True)
    (a.output/'models.json').write_text(json.dumps(models,indent=2)+'\n',encoding='utf-8')
    (a.output/'results.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    # A false merge must have a concrete word witnessing the added language.
    bad=None
    d=cases['mod4'];n=m.lift(d,guard)
    for i in range(n.n):
        for j in range(i+1,n.n):
            candidate=m.merge(n,i,j);cert=m.certificate(d,candidate)
            if not cert['valid']:
                word=cert['word'];assert candidate.accepts(word)==1 and d.accepts(word)==0
                bad=dict(pair=[i,j],word=word,dfa=asdict(d),nfa=asdict(candidate));break
        if bad:break
    assert bad
    (a.output/'negative.json').write_text(json.dumps(bad,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
