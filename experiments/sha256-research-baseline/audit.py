"""Read-only checks of old assets, plus diffs and source hashes for this new run."""
import difflib, hashlib, json, platform, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
report = {'python':platform.python_version(), 'past_asset_checks':[], 'rebuild':[]}
# Integrity checks do not imply independent re-execution of previous experiments.
for name in ['rounding-residual-gate','targeted-window-search','local-mixing-observer-audit']:
    folder=WORK/'tmp'/name
    inv=json.loads((folder/'inventory.json').read_text(encoding='utf-8-sig'))
    rows=[]
    for entry in inv:
        if 'path' not in entry or 'sha256' not in entry: raise ValueError('Unknown inventory schema')
        p=folder/entry['path'].replace('\\','/')
        actual=sha(p) if p.is_file() else None
        rows.append({'path':entry['path'],'expected':entry['sha256'].lower(),'actual':actual,'match':actual==entry['sha256'].lower()})
    report['past_asset_checks'].append({'candidate':name,'entries':rows,'all_match':all(r['match'] for r in rows),'rerun':False})
for f in ['sha256.js','hash.js','LICENSE','package.json']:
    original=WORK/'data/extracted/wobfuscator-Projects-debug-7z/debug/node_modules/sha.js'/f
    assert sha(original)==sha(ROOT/'vendor'/f),f
report['vendor_origin']='data/extracted/wobfuscator-Projects-debug-7z/debug/node_modules/sha.js'
report['vendor_originals_match']=True
for folder in ['artifacts','artifacts-recheck']:
    p=ROOT/folder
    if not p.exists(): continue
    m=json.loads((p/'manifest.json').read_text())
    for row in m['files']:
        assert sha(p/row['file'])==row['sha256']
        assert sha(p/row['source'])==row['source_sha256']
    before=(p/'plain.wat').read_text(); after=(p/'mba-add.wat').read_text()
    (p/'plain-to-mba.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='plain.wat',tofile='mba-add.wat')),encoding='utf-8')
    for name in ['plain','mba-add']:
        original=(p/(name+'.raw.wat')).read_text()
        for opt in ['O2','O3']:
            modified=(p/(name+'.'+opt+'.wat')).read_text()
            (p/(name+'.raw-to-'+opt+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),modified.splitlines(True),fromfile=name+'.raw.wat',tofile=name+'.'+opt+'.wat')),encoding='utf-8')
    recovery=p/'recovery'
    if recovery.exists():
        for b in recovery.glob('*.before.wat'):
            a=b.with_name(b.name.replace('.before.wat','.after.wat'))
            b.with_suffix('.diff').write_text(''.join(difflib.unified_diff(b.read_text().splitlines(True),a.read_text().splitlines(True),fromfile=b.name,tofile=a.name)),encoding='utf-8')
if (ROOT/'artifacts-recheck/manifest.json').exists():
    m=json.loads((ROOT/'artifacts/manifest.json').read_text())
    for r in m['files']:
        same=sha(ROOT/'artifacts'/r['file'])==sha(ROOT/'artifacts-recheck'/r['file'])
        assert same
        report['rebuild'].append({'file':r['file'],'identical':same})
report['git']=subprocess.run(['git','log','-1','--format=%H'],cwd=WORK,text=True,capture_output=True,check=True).stdout.strip()
report['scope']='Current working files are mostly uncommitted; hashes, not initial Git commit, identify experiments. Integrity checks of old results are not reruns.'
save(ROOT/'audit.json',report)
save(ROOT/'inventory.json',[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='inventory.json'])
print(json.dumps({'old_inventories':[{'name':r['candidate'],'files':len(r['entries']),'all_match':r['all_match']} for r in report['past_asset_checks']],'rebuild':len(report['rebuild'])}))
