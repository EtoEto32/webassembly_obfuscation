import copy
import json
from pathlib import Path
import re
import sys
import prototype as p


def main(main_dir,dest):
    folder=Path(main_dir).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));replay=[];interpreter=[];attacker=p.recovery()
    for row in manifest['targets']:
        c=manifest['fixtures'][row['name']];data=bytes(c['data']);ops=c['ops'];dst=out/row['file']
        if row['mode']=='recovered':attacker.recover(out/row['file'].replace('.recovered.wasm','.wasm'),dst)
        elif row['opt']=='raw':
            if row['mode']=='plain':p.q.compile(p.base.wat(data,ops),dst)
            else:p.transform(folder/(row['name']+'.source.wasm'),dst,row['mode'],row['seed'])
        else:p.q.w.tool('wasm-opt',[out/row['file'].replace('.O3.','.raw.'),'-O3','--enable-bulk-memory','-o',dst])
        if dst.read_bytes()!=(folder/row['file']).read_bytes():raise AssertionError('replay differs')
        replay.append(row['file'])
        if row['mode']=='bad':continue
        actions=[0xffffffff,*range(len(ops)),len(ops),0xffffffff];mod=p.q.read(dst);logical=bytearray(data);expected=[]
        for j,fail in enumerate(actions):
            for k,(d,s,n) in enumerate(ops):
                if fail==k:break
                logical[d:d+n]=logical[s:s+n]
            value=2166136261
            for b in logical:value=((value^b)*16777619)&0xffffffff
            expected.append(value)
            mod+=p.q.w.parse(f'(module (func (export "step{j}") (call 0 (i32.const {fail}))) (func (export "state{j}") (result i32) (call 1)))')[1:]
        for i in [*range(len(data)),len(data),65535]:mod+=p.q.w.parse(f'(module (func (export "byte{i}") (result i32) (i32.load8_u (i32.const {i}))))')[1:]
        probe=out/(dst.stem+'.interp.wasm');p.q.compile(p.q.w.emit(mod),probe);log=p.q.w.tool('wasm-interp',[probe,'--run-all-exports'])
        probe.with_suffix('.log').write_text(log,encoding='utf-8')
        actual=[int(x) for x in re.findall(r'state\d+\(\) => i32:(\d+)',log)]
        if actual!=expected:raise AssertionError('digest mismatch')
        for j,fail in enumerate(actions):
            line=next(x for x in log.splitlines() if x.startswith(f'step{j}()'))
            if ('error:' in line)!=(fail<len(ops)):raise AssertionError('trap mismatch')
        physical=p.m.apply([int(x) for x in row['meta']['matrix']],logical)
        values=[(int(i),int(x)) for i,x in re.findall(r'byte(\d+)\(\) => i32:(\d+)',log)]
        if len(values)!=len(data)+2:raise AssertionError('missing probe')
        if any(x!=(physical[i] if i<len(data) else 0) for i,x in values):raise AssertionError('memory mismatch')
        interpreter.append(dict(file=row['file'],calls=len(actions),traps=len(ops),memory_probes=len(values)))
    controls=[];original=p.q.read(folder/'swap16.source.wasm')
    for name in ('exported-memory','memory-grow','parameter-store'):
        mod=copy.deepcopy(original);f=next(e for e in mod[1:] if e[0]=='func')
        if name=='exported-memory':mod.append(['export','"memory"',['memory','0']])
        elif name=='memory-grow':f.append(['drop',['memory.grow',['i32.const','1']]])
        else:f.append(['i32.store8',['i32.const','0'],['local.get','0']])
        src=out/(name+'.wasm');p.q.compile(p.q.w.emit(mod),src)
        try:p.transform(src,out/(name+'-transformed.wasm'))
        except ValueError as ex:controls.append(dict(name=name,status='unsupported',reason=str(ex)))
        else:raise AssertionError('unsupported input accepted')
    result=dict(replay=replay,interpreter=interpreter,calls=sum(x['calls'] for x in interpreter),traps=sum(x['traps'] for x in interpreter),memory_probes=sum(x['memory_probes'] for x in interpreter),mismatches=0,rejected=controls)
    p.q.save(out/'audit.json',result);print(json.dumps({k:result[k] for k in ('calls','traps','memory_probes','mismatches')}))


if __name__=='__main__':main(*sys.argv[1:])
