import argparse,json,random,statistics
from pathlib import Path
import prototype as p
import attack
import run as runner

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    jobs=[(name,mode,rep) for name in runner.NAMES for mode in ('fixed','full','transport') for rep in range(7)]
    random.Random(221125).shuffle(jobs);rows=[]
    for name,mode,rep in jobs:
        tag=f'{name}-{mode}-{rep}'
        stats=attack.recover(main/f'{name}.{mode}.O3.wasm',out/(tag+'.wasm'),out/tag)
        assert (out/(tag+'.wasm')).read_bytes()==(main/f'{name}.{mode}.O3.recovered.wasm').read_bytes()
        rows.append(dict(name=name,mode=mode,rep=rep,**stats));p.q.save(out/'measurements.json',rows)
    summary=[]
    for name in runner.NAMES:
        modes={}
        for mode in ('fixed','full','transport'):
            values=[x['total_ms'] for x in rows if x['name']==name and x['mode']==mode]
            modes[mode]=dict(median=statistics.median(values),range=[min(values),max(values)])
        summary.append(dict(name=name,modes=modes,transport_over_fixed=modes['transport']['median']/modes['fixed']['median']))
    p.q.save(out/'summary.json',dict(rows=summary,repetitions=7,order_seed=221125,scope='O3 end-to-end helper identification and candidate rewrite, including WABT, Node startup and output compilation; no universal-equivalence proof. Same 1024 helper calls in every attempt.'))
    runner.pin(out);print(json.dumps(summary))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
