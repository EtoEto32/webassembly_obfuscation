import argparse,hashlib,json,platform,re,shutil,statistics,sys
from pathlib import Path
from experiment import ROOT,HERE,TOOL,OPT,SM,wt,dump,sha
EXPECTED_PAPER='7d31f76903832dc6923895a3342361349ddbeb646c863089f5ec2adfb22b851c'
def main(out):
 out.mkdir(parents=True,exist_ok=False);errors=[];hashes=0;validated=0;medians=0;engine=wt.Engine()
 for relative in ['heap-observer/performance-v1','heap-observer/performance-v2','heap-observer/bounds-v1','heap-observer/priors-v1','boundary-alias/caller-priors-v1']:
  src=ROOT/'results'/relative
  for item in json.loads((src/'manifest.json').read_text()):
   if 'sha256' not in item:continue
   hashes+=1
   if sha(src/item['file'])!=item['sha256']:errors.append(dict(kind='hash',file=relative+'/'+item['file']))
  if relative.startswith('heap-observer/performance') or relative=='heap-observer/bounds-v1':
   for p in src.glob('*.wasm'):
    try:wt.Module(engine,p.read_bytes());validated+=1
    except Exception as e:errors.append(dict(kind='validation',file=p.name,error=str(e)))
  if relative.startswith('heap-observer/performance'):
   rows=json.loads((src/'rows.json').read_text());report=json.loads((src/'report.json').read_text())
   for s in report['summary']:
    measured=statistics.median(statistics.median(r['samples']) for r in rows if r['n']==s['n'] and r['mode']==s['mode']);medians+=1
    if measured!=s['median_ns']:errors.append(dict(kind='median',file=relative,mode=s['mode'],n=s['n']))
 src=ROOT/'results/heap-observer/bounds-v1';rows=json.loads((src/'rows.json').read_text());comparisons=json.loads((src/'report.json').read_text())['comparisons']
 for c in comparisons:
  pair=[r for r in rows if (r['family'],r['level'],r['cap'],r['engine'])==(c['family'],c['level'],c['cap'],c['engine'])]
  same=pair[0]['result']['snapshot']==pair[1]['result']['snapshot']
  if same!=c['equal'] or same!=c['expected_equal']:errors.append(dict(kind='bounds-comparison',comparison=c))
 paper=sha(ROOT/'paper/main.tex')
 if paper!=EXPECTED_PAPER:errors.append(dict(kind='paper-changed',sha256=paper))
 sources=[];broken=[]
 for directory in [HERE,ROOT/'research/boundary-alias']:
  for p in directory.rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   relative=p.relative_to(ROOT);dest=out/'sources'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);sources.append(dict(file=str(relative).replace('\\','/'),sha256=sha(p)))
   if p.suffix=='.md':
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
     if '://' in link or link.startswith('#'):continue
     target=link.split('#')[0]
     if target and not (p.parent/target).exists():broken.append(dict(file=str(relative),target=target))
 if broken:errors.append(dict(kind='broken-links',links=broken))
 dump(out/'source-manifest.json',sources)
 report=dict(platform=platform.platform(),machine=platform.machine(),python=sys.version,additional_hash_entries=hashes,additional_validated_binaries=validated,recomputed_performance_medians=medians,bounds_comparisons=len(comparisons),source_files=len(sources),broken_links=broken,paper_sha256=paper,tool_sha256=sha(TOOL),optimizer_sha256=sha(OPT),spidermonkey_sha256=sha(SM),account_usage_note='2026-10-27 observed 24% used / 76% remaining; account window, not exact token balance',errors=errors)
 dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=str(p.relative_to(out)).replace('\\','/'),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()]);print(json.dumps(report,indent=2));assert not errors
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
