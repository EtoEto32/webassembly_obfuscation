"""Read-only integrity, reproduction, and local-document-link audit."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/invention-20261018'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit():
    main=BASE/'observation-suite-v2';repro=BASE/'observation-reproduction-v1';verified={}
    for d in (main,repro):
        inv=read(d/'inventory.json')
        for name,expected in inv.items():
            assert (d/name).is_file(),name
            assert sha(d/name)==expected,(d.name,name)
        s=read(d/'summary.json')
        for k,v in {'variants':75,'correctness_per_export':54600,'correctness_export_calls':163800,
                    'trap_cases':26250,'mismatches':0,'cross_engine_cases':2400,'cross_engine_mismatches':0,
                    'targets_recovered':60,'no_target':15,'output_expressions_proved':75,'normalized_outputs':75,
                    'compilation_messages_during_timing':0}.items():assert s[k]==v,(d.name,k)
        verified[d.name]=len(inv)
    mm={a['id']:a['sha256'] for a in read(main/'manifest.json')['artifacts']}
    rm={a['id']:a['sha256'] for a in read(repro/'manifest.json')['artifacts']}
    assert mm==rm
    docs=[ROOT/'README.md',ROOT/'paper-draft.md',*(ROOT/'research').glob('*.md'),
          ROOT/'research/observation-synthesis/README.md',BASE/'README.md']
    links=0
    for p in docs:
        prose=re.sub(r'(?ms)^```.*?^```\s*$','',p.read_text(encoding='utf-8-sig'))
        prose=re.sub(r'`[^`]*`','',prose)
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',prose):
            if '://' in target or target.startswith('#'):continue
            target=target.split('#')[0]
            if not target:continue
            assert (p.parent/target).exists(),(str(p),target)
            links+=1
    result={'inventory_files_verified':verified,'reproduced_binary_hashes':len(mm),'local_links_checked':links,
      'scope':'Checks saved assets and report consistency; not an independent rerun of every test or a proof of security.'}
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':audit()
