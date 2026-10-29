"""Independent decoding, golden checks, rejection cases, and replay of saved artifacts."""
import argparse,json,subprocess,collections
from pathlib import Path
from experiment import ROOT,HERE,TOOL,wt,dump,sha

def uleb(data,pos):
 n=0;s=0
 while True:
  b=data[pos];pos+=1;n|=(b&127)<<s
  if b<128:return n,pos
  s+=7
def type_entries(path):
 data=path.read_bytes();pos=8
 while pos<len(data):
  code=data[pos];size,start=uleb(data,pos+1);end=start+size
  if code==1:
   count,body=uleb(data,start);return count,data[body:end]
  pos=end
 return 0,b''
def main(out):
 out.mkdir(parents=True,exist_ok=False);errors=[];hashes=0;reencoded=0;validated=0;prefixes=0;engine=wt.Engine();generated=[]
 for folder in ['probe-v2','generated-v1']:
  src=ROOT/'results/heap-observer'/folder
  for item in json.loads((src/'manifest.json').read_text()):
   hashes+=1
   if sha(src/item['file'])!=item['sha256']:errors.append(dict(kind='hash',folder=folder,file=item['file']))
  for p in src.glob('*.wasm'):
   try:wt.Module(engine,p.read_bytes());validated+=1
   except Exception as e:errors.append(dict(kind='wasmtime-validation',file=p.name,error=str(e)))
  metas=json.loads((src/('metadata.json' if folder=='probe-v2' else 'generation.json')).read_text())
  for m in metas:
   if m['status']!='generated':continue
   if folder=='probe-v2':raw=src/(m['name']+'-base-O0.wasm');helper=src/(m['name']+'.observer.wasm')
   else:raw=src/('%d-O0.wasm'%m['seed']);helper=src/('%d.observer.wasm'%m['seed'])
   new=out/('replay-'+folder+'-'+helper.name);p=subprocess.run([str(TOOL),str(raw),str(new)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);reencoded+=1
   if meta['status']!='generated' or new.read_bytes()!=helper.read_bytes():errors.append(dict(kind='reencode',file=helper.name))
   before,entries=type_entries(raw);after,allentries=type_entries(helper)
   if not allentries.startswith(entries) or after!=before+m['helper_functions']:errors.append(dict(kind='type-prefix',file=helper.name))
   else:prefixes+=1
 rows=json.loads((ROOT/'results/heap-observer/probe-v2/rows.json').read_text());gold=[]
 for r in rows:
  if r['level']!='O0' or r['variant']!='base':continue
  snap=r['result']['snapshot'];obj=snap['objects'];name=r['name'];expected={
   'scalar':[41,{'bigint':'-9223372036854775808'},{'f32':2147483648},{'f64':'3ff8000000000000'}],
   'packed':[255,65535], 'array':[9,9,9], 'deep':[{'ref':1}], 'alias':[{'ref':1},{'ref':1}],
   'cycle':[{'ref':0},41], 'recgroup':[None,41], 'subtype':[7,41], 'nan-positive':[{'f32':'nan'},{'f64':'nan'}]}[name]
  passed=obj[0]['fields']==expected and snap['roots']==[{'ref':0},{'ref':0}]
  if name=='deep':passed=passed and obj[1]['fields']==[41]
  if name=='alias':passed=passed and len(obj)==2 and obj[1]['fields']==[9]
  if name=='cycle':passed=passed and len(obj)==1
  gold.append(dict(name=name,engine=r['engine'],passed=passed))
  if not passed:errors.append(dict(kind='golden',name=name,engine=r['engine']))
 rejections=[]
 fixtures={'invalid':b'bad','oversize':b'\0'*1048577,'v128':wt.wat2wasm('(module (type (struct (field v128))))'),'exception':wt.wat2wasm('(module (type (struct (field exnref))))'),'shared':wt.wat2wasm('(module (type (shared (struct (field i32)))))')}
 for name,data in fixtures.items():
  path=out/(name+'.input');path.write_bytes(data);dest=out/(name+'.output.wasm');p=subprocess.run([str(TOOL),str(path),str(dest)],capture_output=True,text=True,timeout=10);r=json.loads(p.stdout);passed=r['status']=='rejected' and not dest.exists();rejections.append(dict(name=name,passed=passed,**r))
  if not passed:errors.append(dict(kind='rejection',name=name))
 source=ROOT/'results/heap-observer/generated-v1';rs=json.loads((source/'rows.json').read_text());baseline=json.loads((source/'report.json').read_text())['baseline'];copy_checks=0
 for p in source.glob('*-O*.wasm'):
  copy_checks+=1
  if p.read_bytes()!=(ROOT/'results/boundary-alias/caller-v1'/p.name).read_bytes():errors.append(dict(kind='target-changed',file=p.name))
 for r in rs:
  txt=(source/('%d-%s-%s.stdout'%(r['seed'],r['level'],r['engine']))).read_text();line=next(x[len('[heap-study] '):] for x in txt.splitlines() if x.startswith('[heap-study] '))
  if json.loads(line)!=r['study']:errors.append(dict(kind='raw-result',seed=r['seed']))
 for b in baseline:
  if not b['calls_equal'] or not b['trace_equal']:errors.append(dict(kind='baseline-change',**b))
 report=dict(manifest_entries=hashes,wasmtime_validated=validated,reencoded_helpers=reencoded,type_section_original_prefixes=prefixes,golden_checks=gold,rejections=rejections,unchanged_target_checks=copy_checks,raw_replays=len(rs),baseline_comparisons=len(baseline),errors=errors)
 dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(report,indent=2));assert not errors
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
