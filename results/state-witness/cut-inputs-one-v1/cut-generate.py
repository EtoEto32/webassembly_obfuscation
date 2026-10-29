"""Generate semantically inert checkpoint opportunities in pinned official seeds."""
import argparse,copy,hashlib,json,shutil,subprocess,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
VOID={'data.drop','elem.drop','memory.init','table.init','memory.copy','table.copy','memory.fill','table.fill','nop'}

def main(source,out,delimiters=2):
    start=time.perf_counter();out.mkdir(parents=True,exist_ok=False);cases=[];skips=[];manifest=json.loads((source/'manifest.json').read_text())
    for row in manifest['rows']:
        if row['status']!='accepted':continue
        m=k.p.read(source/row['source']);funcs=k.p.section(m,'func');types=k.p.section(m,'type')
        for exp in k.p.section(m,'export'):
            if exp[2][0]!='func':continue
            index=int(exp[2][1]);f=funcs[index]
            tid=int(next(x[1] for x in f[1:] if isinstance(x,list) and x[0]=='type'))
            if types[tid][1]!=['func']:continue
            cuts=[(pos,x) for pos,x in enumerate(f) if isinstance(x,list) and x[0] in ('data.drop','elem.drop')]
            if not cuts:continue
            if any(not isinstance(x,list) or x[0] not in VOID|{'type'} for x in f[1:]) or k.p.section(m,'global'):
                skips.append({'source':row['source'],'function':index,'reason':'restricted void-body/global profile'});continue
            # Only immutable zero-argument constant functions may be invoked by the table oracle.
            constants={i:int(fn[-1][1]) for i,fn in enumerate(funcs) if
                       [x for x in fn[1:] if x[0] not in k.p.DECL]==[fn[-1]] and fn[-1][0]=='i32.const'}
            refs=[int(x) for seg in k.p.section(m,'elem') for x in seg[seg.index('func')+1:]]
            if any(i not in constants for i in refs):
                skips.append({'source':row['source'],'reason':'table functions not pure constant tags'});continue
            for pos,op in cuts:
                n=len(cases);folder=out/f'case-{n:02}';folder.mkdir();base=copy.deepcopy(m)
                added_memory=not k.p.section(base,'memory')
                if added_memory:base.append(['memory','1','1'])
                if not any(e[1]=='"memory"' for e in k.p.section(base,'export')):base.append(['export','"memory"',['memory','0']])
                for t in range(len(k.p.section(base,'table'))):base.append(['export',f'"__audit_table_{t}"',['table',str(t)]])
                original=folder/'original.wasm';k.p.compile_wat(k.p.w.emit(base),original)
                changed=copy.deepcopy(base);target=k.p.section(changed,'func')[index]
                loop=k.p.expr('(loop (br_if 0 (i32.const 0)))');target[pos+1:pos+1]=[copy.deepcopy(loop) for _ in range(delimiters)]
                cut=folder/'cut.wasm';k.p.compile_wat(k.p.w.emit(changed),cut)
                origobs=folder/'original-observed.wasm';k.transform(original,origobs,True)
                observed=folder/'cut-observed.wasm';meta=k.transform(cut,observed,True)
                entries=[]
                for backend,exe in [('migrate',ROOT/'.tools/wasm-migrate-build/target/release/wasm-migrate-target.exe'),
                                    ('weave',ROOT/'.tools/weave-build/target/release/weave-probe.exe')]:
                    for kind,src in [('plain',cut),('observed',observed)]:
                        dest=folder/(backend+'-'+kind+'.wasm');cmd=[str(exe),str(src),str(dest)]
                        if backend=='migrate':cmd.append(str(index))
                        try:
                            r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
                            item={'backend':backend,'kind':kind,'output':dest.relative_to(out).as_posix(),'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
                            if r.returncode==0:
                                try:k.p.tool('wasm-validate',[dest]);item['status']='valid'
                                except RuntimeError as e:item.update({'status':'invalid-output','error':str(e)})
                            else:item['status']='transform-failure'
                        except subprocess.TimeoutExpired:item={'backend':backend,'kind':kind,'status':'transform-timeout'}
                        entries.append(item)
                cases.append({'id':n,'source':row['source'],'sourceSha256':hashlib.sha256((source/row['source']).read_bytes()).hexdigest(),
                  'entry':json.loads(exp[1]),'definedFunction':index,'cutAt':pos,'operation':op,'addedMemory':added_memory,
                  'guestPages':int(k.p.section(base,'memory')[0][1]),'tables':len(k.p.section(base,'table')),'tags':constants,
                  'original':original.relative_to(out).as_posix(),'originalObserved':origobs.relative_to(out).as_posix(),
                  'cut':cut.relative_to(out).as_posix(),'observed':observed.relative_to(out).as_posix(),'observer':meta,'entries':entries})
    for name in ('cut-generate.py','prototype.py','observer.cjs'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(ROOT/'.tools/weave-build/js/weave.mjs',out/'weave.mjs')
    executables=[ROOT/'.tools/wasm-migrate-build/target/release/wasm-migrate-target.exe',ROOT/'.tools/weave-build/target/release/weave-probe.exe']
    (out/'manifest.json').write_text(json.dumps({'cases':cases,'skips':skips,'delimiters':delimiters,
       'generationSeconds':time.perf_counter()-start,'executableHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in executables},
       'inputHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps({'cases':len(cases),'skips':len(skips),'valid':sum(e['status']=='valid' for c in cases for e in c['entries'])}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--delimiters',type=int,choices=[1,2],default=2);v=a.parse_args();main(v.source,v.out,v.delimiters)
