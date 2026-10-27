import argparse,copy,json,re,shutil
from pathlib import Path
import prototype as p
import recover
def oracle(n,x,y,pars):
    c1,c2,r=pars;mask=p.MASK;n&=31;stack=[];x&=mask;y&=mask
    def rot(x,k):return ((x<<k)|(x>>(32-k)))&mask
    for d in range(n,0,-1):stack.append(d);x,y=y,(x^((rot(y,r)+d*c1)&mask))&mask
    x^=c1;y=(y+c2)&mask
    for d in reversed(stack):x=(x+d*c2)&mask;y^=rot(d,5)
    return x|(y<<32)
def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((main/'manifest.json').read_text());fixtures={r['name']:r['parameters'] for r in manifest['fixtures']};rows=[]
    probes=[(0,0,0),(1,1,0xffffffff),(7,0x80000000,0x7fffffff),(31,0xffffffff,0x80000000),(32,123,456),(0xffffffff,0,1),(8,17,257),(16,0xaaaaaaaa,0x55555555)]
    for b in manifest['binaries']:
        dst=out/b['file'];name=b['name'];mode=b['mode'];opt=b['opt']
        if mode.endswith('-recovered'):recover.recover(out/(name+'.'+mode[:-10]+'.'+opt+'.wasm'),dst)
        elif opt=='O3':p.tool('wasm-opt',[out/(name+'.'+mode+'.raw.wasm'),'-O3','-o',dst])
        elif mode=='plain':p.compile(p.source_text(*fixtures[name]),dst)
        else:p.transform(out/(name+'.plain.raw.wasm'),dst,mode)
        if p.digest(dst)!=b['sha256']:raise AssertionError('byte mismatch '+b['file'])
        row=dict(file=b['file'],byte_equal=True)
        if not b['negative']:
            m=p.read(dst)
            for i,values in enumerate(probes):m.append(p.sx.parse('(module (func (export "probe'+str(i)+'") (result i64) (call 1 '+' '.join(p.c(v) for v in values)+')))')[1])
            test=out/(b['file']+'.probe.wasm');p.compile(p.sx.emit(m),test)
            text=p.tool('wasm-interp',[test,'--run-all-exports']).decode();got={int(i):int(v)&((1<<64)-1) for i,v in re.findall(r'probe(\d+)\(\) => i64:(-?\d+)',text)}
            expect={i:oracle(*values,fixtures[name]) for i,values in enumerate(probes)}
            if got!=expect:raise AssertionError(dict(file=b['file'],got=got,expect=expect,log=text))
            row['interpreter_calls']=len(probes);row['stdout']=text
        rows.append(row)
    rejections=[]
    plain=p.read(out/'wide.plain.raw.wasm');dynamic=p.read(out/'wide.dynamic.raw.wasm')
    variants=[]
    memory=copy.deepcopy(plain);memory.append(['memory','1']);variants.append(('source-memory',memory,'transform'))
    bad_profile=copy.deepcopy(plain);funcs=[x for x in bad_profile[1:] if x[0]=='func'];first=next(x for x in p.walk(funcs[0]) if x[0]=='i32.xor');first[0]='i32.or';variants.append(('source-operation',bad_profile,'transform'))
    memory2=copy.deepcopy(dynamic);memory2.append(['memory','1']);variants.append(('recovery-memory',memory2,'recover'))
    nondecrease=copy.deepcopy(dynamic);call=next(x for x in p.walk([x for x in nondecrease[1:] if x[0]=='func'][0]) if x[0]=='call');call[2]=['local.get','0'];variants.append(('nondecreasing-call',nondecrease,'recover'))
    basecall=copy.deepcopy(plain);f=[x for x in basecall[1:] if x[0]=='func'][0];then=next(x for x in p.walk(f) if x[0]=='then');then[1:]=[['call','0',['i32.sub',['local.get','0'],['i32.const','1']],['local.get','1'],['local.get','2']]];variants.append(('recursive-base',basecall,'recover'))
    wrapper=copy.deepcopy(dynamic);f=[x for x in wrapper[1:] if x[0]=='func'][1];f[-1]=['i64.xor',f[-1],['i64.const','1']];variants.append(('changed-wrapper',wrapper,'recover'))
    for name,mod,kind in variants:
        file=out/(name+'.wasm');p.compile(p.sx.emit(mod),file)
        try:
            if kind=='transform':p.transform(file,out/(name+'.accepted.wasm'),'dynamic')
            else:recover.analyse(file)
        except p.Unsupported as e:rejections.append(dict(name=name,valid_wasm=True,rejected=True,reason=str(e)))
        else:raise AssertionError('unexpected acceptance '+name)
    result=dict(rows=rows,rejections=rejections,regenerated=len(rows),interpreter_calls=sum(x.get('interpreter_calls',0) for x in rows),scope='finite independent execution and regenerated artifacts; not machine checked proof')
    p.save(out/'audit.json',result);p.save(out/'commands.json',p.LOG)
    for name in ('prototype.py','recover.py','audit.py'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({k:result[k] for k in ('regenerated','interpreter_calls','rejections')}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
