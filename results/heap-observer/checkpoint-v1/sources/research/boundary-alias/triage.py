"""Keep exact log differences; separately normalize trap messages/stack locations."""
import argparse,difflib,json
from pathlib import Path
from experiment import dump,sha
def normalized(lines):
 result=[]
 for s in lines:
  if s.startswith('[boundary-alias] ') or s.startswith('    at '):continue
  if s.startswith('exception thrown: RuntimeError:'):s='exception thrown: RuntimeError'
  result.append(s)
 return result
def main(source,out):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for seed in range(64):
  for en in ['node','spidermonkey']:
   a=(source/('%d-O0-%s.stdout'%(seed,en))).read_text().splitlines();b=(source/('%d-O3-%s.stdout'%(seed,en))).read_text().splitlines()
   diff=[s for s in difflib.ndiff(a,b) if s.startswith(('- ','+ '))]
   rows.append(dict(seed=seed,engine=en,raw_equal=not diff,normalized_equal=normalized(a)==normalized(b),exact_differences=diff))
 report=dict(pairs=len(rows),raw_differences=sum(not r['raw_equal'] for r in rows),normalized_differences=sum(not r['normalized_equal'] for r in rows),normalization='Remove Node stack location lines; compare RuntimeError class separately from its unspecified diagnostic text. Preserve instantiation outcome, TypeError, RangeError, event order and ordinary outputs.')
 dump(out/'rows.json',rows);dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in out.iterdir() if p.is_file()]);print(json.dumps(report,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
