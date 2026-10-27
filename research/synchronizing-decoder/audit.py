import json, subprocess, sys
from pathlib import Path
import prototype as p
import recover as r

def oracle(x,y,cs):
    mask=(1<<32)-1
    def rot(v,n):return ((v<<n)|(v>>(32-n)))&mask
    z=x
    for a,b,c,d in cs:
        z=rot(z,5)^y;aa,bb=(a,b) if z&1 else (c,d);z=(z+aa*y+bb)&mask;y^=rot(z,13)
    return (z^y)&mask

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((folder/'manifest.json').read_text());cases=json.loads((folder/'cases.json').read_text());trans=json.loads((folder/'transforms.json').read_text())
    proven=0;nonpotential=0;small=0
    for record in trans:
        if record['mode']=='bad':continue
        for info in record['gates']:
            expected=[0,info['target_a'],info['target_b']]
            assert all(v==expected for v in p.model.summarize(info));proven+=1
            witness=info['nonpotential_selfloop_witness'];assert witness
            i,j=witness['states'];n=info['n'];assert info['next'][n+i]==i and info['next'][n+j]==j
            assert (info['a'][n+i],info['b'][n+i])!=(info['a'][n+j],info['b'][n+j]);nonpotential+=1
        if record['mode']=='sync':
            info=record['gates'][0];n=info['n']
            for x in range(16):
                for y in range(16):
                    for start in range(n):
                        z=x;state=start
                        for letter in info['word']:
                            k=letter*n+state;z=(z+info['a'][k]*y+info['b'][k])&15;state=info['next'][k]
                        assert z==(x+info['target_a']*y+info['target_b'])&15 and state==0;small+=1
    inputs=[(0,0),(0,1),(1,0),(0xffffffff,0xffffffff),(0x80000000,0x7fffffff),(0x12345678,0x9abcdef0)];cross=[];replay=[];rejections=[]
    import re
    for row in rows:
        src=folder/row['file']
        if row.get('negative'):
            try:r.recover(src,out/(src.stem+'-should-not-recover.wasm'))
            except r.Unsupported as exc:rejections.append({'file':row['file'],'reason':str(exc)})
            else:raise AssertionError('negative accepted')
            continue
        if row['mode'] in ('fixed','sync'):
            f=out/(src.stem+'-replay.wasm');inf=r.recover(src,f);same=p.q.digest(f)==p.q.digest(folder/(src.stem+'-recovered.wasm'));assert same;replay.append({'file':row['file'],'byte_identical':same,'analysis_ms':inf['analysis_ms']})
        mod=p.q.read(src);index=next(e[2][1] for e in mod[1:] if e[0]=='export')
        mod=[mod[0],*[e for e in mod[1:] if e[0]!='export']]
        wrappers=''.join('(func (export "p%d") (result i32) (call %s %s %s))'%(i,index,p.q.w.emit(p.c(x)),p.q.w.emit(p.c(y))) for i,(x,y) in enumerate(inputs))
        f=out/(src.stem+'-interp.wasm');p.q.compile(p.q.w.emit(mod)[:-1]+wrappers+')',f);log=p.q.w.tool('wasm-interp',[f,'--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf-8')
        values=[int(v) for v in re.findall(r'p\d+\(\) => i32:(\d+)',log)];expected=[oracle(x,y,cases[row['name']]['coefficients']) for x,y in inputs];assert values==expected,(row,values,expected)
        cross.append({'file':row['file'],'values':values})
    text,_=p.source(1,2)
    for name,source in [('memory-export',text.replace('(module','(module (memory (export "memory") 1)',1)),('division',text.replace('i32.rotl','i32.div_u')),('no-affine','(module (func (export "run") (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1))))')]:
        f=out/(name+'.wasm');p.q.compile(source,f)
        try:p.transform(f,out/(name+'-result.wasm'),4,1,'sync')
        except ValueError as exc:rejections.append({'file':f.name,'reason':str(exc)})
        else:raise AssertionError('source accepted')
    mod=p.q.read(folder/'round1-n4-sync-raw.wasm');call=next(e for e in p.q.walk(mod) if e[0]=='call');call[4]=['i32.rem_u',['i32.rem_u',p.local(0),p.c(0)],p.c(4)]
    f=out/'trapping-state-expression.wasm';p.q.compile(p.q.w.emit(mod),f)
    try:r.recover(f,out/'trapping-state-should-not-recover.wasm')
    except r.Unsupported as exc:rejections.append({'file':f.name,'reason':str(exc)})
    else:raise AssertionError('trapping expression discarded')
    result={'gate_certificates':proven,'nonpotential_witnesses':nonpotential,'small_width_pairs':small,'wabt_conditions':len(cross),'wabt_calls':len(cross)*len(inputs),'wabt':cross,'replays':replay,'rejections':rejections}
    p.q.save(out/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('wabt','replays','rejections')}))
if __name__=='__main__':main(*sys.argv[1:])
