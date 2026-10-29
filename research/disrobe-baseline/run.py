"""Pinned external-tool baseline. Process success is not semantic recovery."""
import hashlib,json,pathlib,platform,random,re,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
DIS=ROOT/'.tools/disrobe-v0.10.6/disrobe-v0.10.6-x86_64-pc-windows-msvc/disrobe.exe'
WABT=ROOT/'.tools/wabt-1.0.42/bin'
LISTS=ROOT/'results/invention-20261021/notdec-baseline-v1'
SCALAR=ROOT/'results/invention-20261023/residue-wrap-v2'

def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return str(path.relative_to(ROOT)).replace('\\','/')
def command(args,prefix,timeout=30):
    start=time.perf_counter()
    try:
        p=subprocess.run([str(a) for a in args],capture_output=True,timeout=timeout)
        record={'status':'success' if p.returncode==0 else 'nonzero_exit','returncode':p.returncode}
        stdout,stderr=p.stdout,p.stderr
    except subprocess.TimeoutExpired as e:
        record={'status':'timeout'};stdout,stderr=e.stdout or b'',e.stderr or b''
    record.update(milliseconds=(time.perf_counter()-start)*1000,command=[str(a) for a in args])
    prefix.with_suffix('.stdout.txt').write_bytes(stdout);prefix.with_suffix('.stderr.txt').write_bytes(stderr)
    save(prefix.with_suffix('.command.json'),record)
    return record,stdout

def model(t,args):
    if t[0]=='p':return args[t[1]]&0xffffffff
    if t[0]=='c':return t[1]&0xffffffff
    a,b=model(t[1],args),model(t[2],args)
    return {'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b}[t[0]]()&0xffffffff

def main(dest):
    out=(ROOT/dest).resolve();out.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for r in json.loads((LISTS/'manifest.json').read_text()):
        tests=json.loads((LISTS/(r['name']+'.tests.json')).read_text())
        jobs.append({'name':r['name'],'group':'list','source':LISTS/(r['name']+'.wasm'),
                     'spec':{'export':'lookup','tests':[{'args':[x],'expected':y} for x,y in tests]}})
    cases=json.loads((SCALAR/'cases.json').read_text());rng=random.Random(20261023)
    edge=[0,1,2,65535,65536,65537,65539,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    inputs=[[a,b] for a in edge for b in edge]+[[rng.getrandbits(32),rng.getrandbits(32)] for _ in range(4096)]
    for r in json.loads((SCALAR/'manifest.json').read_text()):
        if r['mode'] not in ('plain','repair','aligned'):continue
        jobs.append({'name':pathlib.Path(r['file']).stem,'group':'scalar','source':SCALAR/r['file'],
                     'spec':{'export':'run','tests':[{'args':a,'expected':model(cases[r['name']],a)} for a in inputs]}})
    rows=[]
    for job in jobs:
        d=out/job['name'];d.mkdir();spec=d/'tests.json';save(spec,job['spec'])
        row={'name':job['name'],'group':job['group'],'source':rel(job['source']),'source_sha256':sha(job['source']),'outputs':{}}
        cmd,stdout=command(['node',HERE/'check.cjs',job['source'],spec],d/'original-check')
        row['original_check']=json.loads(stdout) if cmd['status']=='success' else cmd
        if row['original_check'].get('mismatches',1):raise RuntimeError('original fixture failed')
        for target in ('c','json','wat'):
            artifact=d/('output.'+target)
            cmd,_=command([DIS,'wasm','decompile',job['source'],'--target',target,'--out',artifact,'--no-cache'],d/('decompile-'+target))
            result={'process':cmd,'generated':artifact.exists()}
            if artifact.exists():
                result.update(bytes=artifact.stat().st_size,sha256=sha(artifact))
                if target=='c':
                    text=artifact.read_text(encoding='utf-8')
                    tail=text[text.rfind('\nint32_t '+job['spec']['export']+'('):]
                    (d/'function.c.txt').write_text(tail,encoding='utf-8')
                    result['function_body_bytes']=len(tail.encode())
                    result['c_recompile']='not_run_no_C_compiler_available'
                if target=='wat':
                    binary=d/'roundtrip.wasm'
                    val,_=command([WABT/'wat2wasm.exe',artifact,'-o',binary],d/'wat-compile')
                    result['wat_compile']=val
                    if val['status']=='success':
                        valid,_=command([WABT/'wasm-validate.exe',binary],d/'wat-validate');result['validation']=valid
                        checked,s=command(['node',HERE/'check.cjs',binary,spec],d/'roundtrip-check')
                        result['check']=json.loads(s) if checked['status']=='success' else checked
                    if job['group']=='list':
                        # Privileged diagnostic only: put original data back into a separate copy.
                        # Never include this in the unassisted recovery success count.
                        original=job['source'].with_suffix('.wat').read_text(encoding='utf-8')
                        segments=re.findall(r'\(data \(i32\.const 64\) "[^"\n]*"\)',original)
                        assert len(segments)==1
                        lifted=artifact.read_text(encoding='utf-8');end=lifted.rfind(')')
                        assert '(data ' not in lifted
                        diag=d/'diagnostic-restored-data.wat'
                        diag.write_text(lifted[:end]+segments[0]+'\n'+lifted[end:],encoding='utf-8')
                        db=diag.with_suffix('.wasm');dc,_=command([WABT/'wat2wasm.exe',diag,'-o',db],d/'diagnostic-compile')
                        if dc['status']=='success':
                            checked,s=command(['node',HERE/'check.cjs',db,spec],d/'diagnostic-check')
                            result['privileged_data_restore_check']=json.loads(s) if checked['status']=='success' else checked
            row['outputs'][target]=result
        rows.append(row);save(out/'results.json',rows)
        print(json.dumps({'name':job['name'],'wat_check':row['outputs']['wat'].get('check')}),flush=True)
    save(out/'environment.json',{'python':sys.version,'platform':platform.platform(),'tool':rel(DIS),'tool_sha256':sha(DIS),'version':subprocess.check_output([str(DIS),'--version']).decode().strip(),'timeout_seconds':30,'date':'2026-10-23','sampling':'single process per target; process time is descriptive, not a performance estimate'})
    frozen=[HERE/'run.py',HERE/'check.cjs',HERE/'plan.md']+[p for p in out.rglob('*') if p.is_file()]
    save(out/'sha256.json',[{'file':rel(p),'sha256':sha(p)} for p in frozen])
    print(json.dumps({'inputs':len(rows),'decompiles':len(rows)*3}))

if __name__=='__main__':main(sys.argv[1])
