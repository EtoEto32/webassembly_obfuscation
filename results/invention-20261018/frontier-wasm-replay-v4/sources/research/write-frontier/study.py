"""Model schedule checks and actual Wasm counterexamples for unsafe merging."""
import argparse
from pathlib import Path
import random
import prototype as p
from run import models,save,command


def execute(ops,base,args,initial):
    memory=bytearray(initial)
    for op in ops:
        address=base+op['offset']
        if address+len(op['bytes'])>len(memory):return True,memory
        for i,(param,byte) in enumerate(op['bytes']):memory[address+i]=(args[param]>>(8*byte))&255
    return False,memory


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rng=random.Random(20261018);records=[];comparisons=0
    for case in range(400):
        specs=[(rng.randrange(25),rng.choice([1,2,4]),rng.randrange(1,6)) for _ in range(rng.randrange(1,13))]
        ops=[dict(offset=x,bytes=[(param,i) for i in range(width)]) for x,width,param in specs];groups=p.frontiers(ops)
        initial=bytes(rng.randrange(256) for _ in range(64));values=[0]+[rng.getrandbits(32) for _ in range(5)]
        modes={m:p.plan(groups,m) for m in ('byte','coalesced','woven0','woven1','random1')}
        assert len(modes['random1'])==len(modes['woven1'])
        for mode,new in modes.items():
            assert p.signature(p.frontiers(new))==p.signature(groups)
            for base in list(range(65))+[0xffffffff]:
                assert execute(ops,base,values,initial)==execute(new,base,values,initial),(case,mode,base)
                comparisons+=1
        records.append(dict(case=case,specs=specs,frontiers=[g['right'] for g in groups],stores={k:len(v) for k,v in modes.items()}))
    save(out/'model-checks.json',dict(programs=400,comparisons=comparisons,mismatches=0,records=records))
    # Exact minimal count for small contiguous runs, independently by a BFS
    # over covered-byte sets, including overlapping intervals.
    counts=[]
    for size in range(1,13):
        full=(1<<size)-1;intervals=[((1<<width)-1)<<start for width in (1,2,4,8) for start in range(size-width+1)]
        layer={0};seen={0};depth=0
        while full not in layer:
            depth+=1;layer={v|i for v in layer for i in intervals}-seen;seen|=layer
        assert len(p.simple_cover(0,size))==depth
        counts.append(dict(bytes=size,min_stores=depth))
    save(out/'minimum-counts.json',counts)
    controls=[]
    for name in ('increasing','descending'):
        m=models()[name];src=out/(name+'.wasm');p.compile_wat(p.plain(m['params'],m['stores']),src);params,ops=p.source(src)
        if name=='increasing':
            image={}
            for op in ops:image.update({op['offset']+i:v for i,v in enumerate(op['bytes'])})
            wrong=p.plan([dict(right=max(image)+1,image=image)],'coalesced');base=65530;label='whole_sequence_fusion_loses_committed_prefix'
        else:
            wrong=[dict(offset=op['offset']+i,bytes=[v]) for op in ops for i,v in enumerate(op['bytes'])];base=65522;label='byte_splitting_creates_partial_store'
        dst=out/(name+'.wrong.wasm');p.compile_wat(p.module(params,wrong),dst)
        controls.append(dict(case=label,original=src.name,wrong=dst.name,args=[base]+[0x01020304*i for i in range(1,params)]))
    save(out/'controls-manifest.json',controls);save(out/'controls.json',__import__('json').loads(command(['node',Path(__file__).parent/'controls.cjs',out])))
    # Source recognition rejects data-dependent addresses and extra effects.
    wat=p.plain(5,models()['increasing']['stores']);rejects=[]
    for label,text in [('load_value',wat.replace('(local.get 1)','(i32.load (local.get 1))',1)),
                       ('different_base',wat.replace('(local.get 0)','(local.get 1)',1)),
                       ('base_mutation',wat.replace('(result i32)','(result i32) (local.set 0 (i32.const 0))',1))]:
        target=out/(label+'.wasm');p.compile_wat(text,target)
        try:p.source(target);raise AssertionError('Accepted unsupported source '+label)
        except ValueError as e:rejects.append(dict(case=label,status='rejected',reason=str(e)))
    save(out/'rejections.json',rejects)
    print(dict(model_programs=400,comparisons=comparisons,unsafe_controls=2,source_rejections=3))


if __name__=='__main__':main()
