"""Independent-engine checks and fresh-process transformation resource measurements."""
import argparse, ctypes, hashlib, json, platform, re, subprocess, sys, time
from pathlib import Path
import transform, suite

def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(t,row):
    if isinstance(t,int):return t&0xffffffff
    if isinstance(t,str):return row[int(t[1:])]&0xffffffff
    a,b=ref(t[1],row),ref(t[2],row)
    return {'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b}[t[0]]()&0xffffffff

def cross(d):
    dest=d/'cross-engine';dest.mkdir()
    plan,manifest=read(d/'plan.json'),read(d/'manifest.json')
    allinputs=read(d/'correctness-inputs.json')
    indices=[0,1,5,35,36,215]+list(range(216,242))
    inputs=[allinputs[i] for i in indices]
    save(dest/'plan.json',{'indices':indices,'inputs':inputs,'engine':'WABT wasm-interp',
                         'scope':'run output only; memory and trap behavior covered separately by V8 tests'})
    rows=[]
    for a in manifest['artifacts']:
        assert h(d/a['file'])==a['sha256']
        m=transform.parse(transform.tool('wasm2wat',[d/a['file'],'--fold-exprs','--generate-names']))
        fn=next(n[2][1] for n in m if isinstance(n,list) and n[:2]==['export','"run"'])
        for i,row in enumerate(inputs):
            args=[['i32.const',str(v if v<2**31 else v-2**32)] for v in row]
            m.append(['func',['export','"case%03d"'%i],['result','i32'],['call',fn,*args]])
        folder=dest/a['program'];folder.mkdir(exist_ok=True)
        p=folder/(a['mode']+'-'+a['level']);wp=Path(str(p)+'.wat');wasm=Path(str(p)+'.wasm')
        wp.write_text(transform.emit(m),encoding='utf-8');transform.tool('wat2wasm',[wp,'-o',wasm])
        raw=transform.tool('wasm-interp',[wasm,'--run-all-exports']);Path(str(p)+'.log').write_text(raw,encoding='utf-8')
        got={int(i):int(v)&0xffffffff for i,v in re.findall(r'case(\d+)\(\) => i32:(\d+)',raw)}
        expected=[ref(plan['programs'][a['program']],row) for row in inputs]
        bad=[i for i,v in enumerate(expected) if got.get(i)!=v]
        rows.append({'id':a['id'],'wrapperSHA256':h(wasm),'checks':len(inputs),'mismatches':bad,'expected':expected,'observed':got})
    save(dest/'results.json',{'engine':transform.tool('wasm-interp',['--version']).strip(),'rows':rows})
    if any(r['mismatches'] for r in rows):raise AssertionError('Cross-engine mismatch')
    print('Cross-engine passed',sum(r['checks'] for r in rows))

def memory():
    if sys.platform!='win32':raise ValueError('Windows process counters only')
    from ctypes import wintypes as w
    class PMC(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(n,ctypes.c_size_t) for n in (
            'PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    k=ctypes.WinDLL('kernel32',use_last_error=True);p=ctypes.WinDLL('psapi',use_last_error=True)
    k.GetCurrentProcess.restype=w.HANDLE
    p.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(PMC),w.DWORD]
    q=PMC();q.cb=ctypes.sizeof(q)
    if not p.GetProcessMemoryInfo(k.GetCurrentProcess(),ctypes.byref(q),q.cb):raise ctypes.WinError(ctypes.get_last_error())
    return {'peakWorkingSetBytes':q.PeakWorkingSetSize,'workingSetBytes':q.WorkingSetSize,'peakPagefileBytes':q.PeakPagefileUsage}

def worker(d,ident,output):
    a=next(a for a in read(d/'manifest.json')['artifacts'] if a['id']==ident)
    before=memory();start=time.perf_counter();output.parent.mkdir(parents=True)
    source=d/a['program']/'plain.wasm'
    if a['mode']=='mba':suite.mba(source,output)
    else:transform.transform(source,output,a['mode'])
    elapsed=time.perf_counter()-start;after=memory()
    if h(output)!=a['sha256']:raise AssertionError('Reproduced artifact differs')
    print(json.dumps({'id':ident,'seconds':elapsed,'before':before,'after':after,'sha256':h(output)}))

def resources(d,label):
    if Path(label).name!=label:raise ValueError('Label must be one directory name')
    dest=d/label;dest.mkdir()
    save(dest/'plan.json',{'repetitions':3,'order':'manifest order, fresh Python process each trial',
      'measurement':'whole Python parent peak working set; child WABT process peaks not measured; wall time includes child tools',
      'platform':platform.platform(),'python':sys.version})
    rows=[]
    for a in read(d/'manifest.json')['artifacts']:
        if a['level']!='raw' or a['mode']=='plain':continue
        for rep in range(3):
            output=dest/a['program']/a['mode']/str(rep)/'output.wasm'
            p=subprocess.run([sys.executable,__file__,str(d),'worker','--id',a['id'],'--output',str(output)],
                  capture_output=True,text=True,timeout=30,check=True)
            rows.append({'rep':rep,**json.loads(p.stdout)})
    save(dest/'results.json',rows);print('Transform trials',len(rows))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('command',choices=('cross','resources','worker'))
    ap.add_argument('--id');ap.add_argument('--output',type=Path);ap.add_argument('--label',default='transform-resources');a=ap.parse_args();d=a.directory.resolve()
    if a.command=='worker':worker(d,a.id,a.output)
    elif a.command=='cross':cross(d)
    else:resources(d,a.label)
