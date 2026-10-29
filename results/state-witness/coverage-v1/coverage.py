"""Bounded static census of pinned, already-local application binaries."""
import argparse,collections,concurrent.futures,hashlib,json,re,shutil,subprocess,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BIN=ROOT/'.tools/wabt-1.0.42/bin'
TARGETS=('data.drop','elem.drop','memory.init','table.init')


def inspect(task):
    path=Path(task['absolute']);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==task['sha256'],path
    row={k:v for k,v in task.items() if k!='absolute'};row['bytes']=len(data)
    if not data:row['status']='empty';return row
    try:valid=subprocess.run([str(BIN/'wasm-validate.exe'),str(path)],capture_output=True,text=True,encoding='utf8',timeout=30)
    except subprocess.TimeoutExpired:row['status']='validation-timeout';return row
    row['validation']={'code':valid.returncode,'stderr':valid.stderr}
    if valid.returncode:row['status']='validation-failure';return row
    proc=subprocess.Popen([str(BIN/'wasm-objdump.exe'),'-d',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    timedout=threading.Event()
    def expire():timedout.set();proc.kill()
    timer=threading.Timer(30,expire);timer.start();seenbytes=0;outputhash=hashlib.sha256();counts=collections.Counter();functions={};current=None;recent=collections.deque(maxlen=5);limit=False;started=time.perf_counter()
    try:
        for raw in proc.stdout:
            outputhash.update(raw);seenbytes+=len(raw)
            if seenbytes>128*1024*1024:limit=True;proc.kill();break
            line=raw.decode('utf8',errors='replace').rstrip();match=re.match(r'^[0-9a-f]+ func\[(\d+)\](.*):$',line)
            if match:current=int(match.group(1));functions[current]={'name':match.group(2).strip(),'counts':collections.Counter(),'sites':[],'directCalls':set()};recent.clear();continue
            if current is None or '|' not in line:continue
            instruction=line.split('|',1)[1].strip();parts=instruction.split();op=parts[0] if parts else ''
            if op in TARGETS:
                counts[op]+=1;functions[current]['counts'][op]+=1
                if len(functions[current]['sites'])<128:functions[current]['sites'].append({'line':line,'prefix':list(recent)})
            elif op=='call' and len(parts)>1 and parts[1].isdigit():functions[current]['directCalls'].add(int(parts[1]))
            recent.append(line)
        code=proc.wait(timeout=5);stderr=proc.stderr.read().decode('utf8',errors='replace')
    finally:
        timer.cancel()
        if proc.poll() is None:proc.kill();proc.wait(timeout=5)
        proc.stdout.close();proc.stderr.close()
    relevant=[]
    for index,f in functions.items():
        if not f['counts']:continue
        f['directCalls']=sorted(f['directCalls']);relevant.append({'functionIndex':index,**f})
    row.update(status='disassembly-timeout' if timedout.is_set() else 'output-limit' if limit else 'disassembly-failure' if code else 'complete',
        counts=dict(counts),functions=relevant,disassembly={'code':code,'stderr':stderr,'bytes':seenbytes,'sha256':outputhash.hexdigest(),'seconds':time.perf_counter()-started})
    return row


def main(out):
    out.mkdir(parents=True,exist_ok=False);tasks=[];records=[]
    for corpus,folder,manifest in [('nowaset','.tools/nowaset-53118203','provenance.json'),('r3','.tools/wasm-r3-bench-review','download.json')]:
        root=ROOT/folder;source=root/manifest;record=json.loads(source.read_text());records.append({'corpus':corpus,'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'commit':record['commit']})
        for row in record.get('files',record.get('rows',[])):
            name=row.get('file',row.get('path'))
            if not name.endswith('.wasm'):continue
            tasks.append({'corpus':corpus,'source':(Path(folder)/name).as_posix(),'absolute':str(root/name),'sha256':row['sha256'],'sourceURL':row.get('sourceURL',row.get('url'))})
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(inspect,tasks):
            rows.append(row)
            if len(rows)%20==0:print(json.dumps({'completed':len(rows),'total':len(tasks)}),flush=True)
    summaries={}
    for corpus in ('nowaset','r3'):
        subset=[r for r in rows if r['corpus']==corpus];complete=[r for r in subset if r['status']=='complete']
        summaries[corpus]={'files':len(subset),'uniqueHashes':len({r['sha256'] for r in subset}),'statuses':dict(collections.Counter(r['status'] for r in subset)),
            'completeWithAnyLifetimeInstruction':sum(bool(r['counts']) for r in complete),
            'completeWithDrop':sum(any(r['counts'].get(n,0) for n in ('data.drop','elem.drop')) for r in complete),
            'counts':{name:sum(r['counts'].get(name,0) for r in complete) for name in TARGETS}}
    result={'rows':rows,'summary':summaries,'provenance':records,'totalFiles':len(rows),'uniqueHashesAcrossCorpora':len({r['sha256'] for r in rows}),
        'scope':'Static instruction presence only. No execution, reachability, or checkpoint applicability claim. Partial output is excluded from complete counts.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for src in (Path(__file__),HERE/'coverage-plan.md'):shutil.copy2(src,out/src.name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(summaries))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
