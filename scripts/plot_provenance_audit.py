"""Plot completed artifact audits independently of ongoing opcode analysis."""
import csv
import hashlib
import json
import os
from acquire import ROOT
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    base=ROOT/'results/provenance'
    inputs=[base/'cryptic-bytes-parents.csv',base/'wasmizer-overlap.json',
            base/'wasmizer-wasmbench-overlap-summary.json']
    with inputs[0].open(encoding='utf-8',newline='') as f:
        parents=list(csv.DictReader(f))
    counts=[len({r['sha256'] for r in parents if r['release_variant']==v})
            for v in ('binaries','binaries-opt')]
    counts.append(len({r['parent_id'] for r in parents}))
    overlap=[r for r in json.loads(inputs[1].read_text()) if r['shared_with_wasmizer']]
    overlap.sort(key=lambda r:(-r['shared_with_wasmizer'],r['dataset']))
    verification=json.loads(inputs[2].read_text())
    assert verification['independent_sources_byte_equal']==verification['shared_sha256']
    fig,(a,b)=plt.subplots(1,2,figsize=(12,5.5),layout='constrained',gridspec_kw={'width_ratios':[1,1.2]})
    a.barh(['Unique binaries\nunoptimized','Unique binaries\noptimized','Source program\ngroups'],counts,
           color=['#315e85','#4e87ab','#da9466'],height=.55)
    a.invert_yaxis();a.set_xscale('log');a.set_xlim(1,70000)
    a.set_title('Cryptic Bytes: counting units',loc='left',fontsize=12)
    a.set_xlabel('Count (log scale)');a.spines[['top','right']].set_visible(False)
    for i,n in enumerate(counts):a.text(n*1.15,i,f'{n:,}',va='center',fontsize=10)
    a.text(0,-.19,'22,508 file occurrences in each release variant.\nSource groups are not malware families.',
           transform=a.transAxes,fontsize=9,color='#555555')
    names=[r['dataset'] for r in overlap]
    vals=[r['shared_with_wasmizer'] for r in overlap]
    b.barh(names,vals,color='#315e85',height=.7)
    b.invert_yaxis();b.set_xlim(0,130);b.spines[['top','right']].set_visible(False)
    b.set_title('Wasmizer: exact overlap with other corpora',loc='left',fontsize=12)
    b.set_xlabel('Shared SHA-256 identities (out of 8,915 Wasmizer binaries)')
    for i,n in enumerate(vals):b.text(n+1.5,i,str(n),va='center',fontsize=9)
    b.text(0,-.19,'127 identities overlap with at least one other corpus.\nCounts overlap across rows; zero-overlap corpora omitted.',
           transform=b.transAxes,fontsize=9,color='#555555')
    fig.suptitle('Public artifact provenance audit | 2026-10-06',fontsize=13)
    output=base/'figures';output.mkdir(exist_ok=True)
    for ext in ['png','svg','pdf']:
        fig.savefig(output/('artifact-provenance-audit.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    (output/'generation.json').write_text(json.dumps({'script':'scripts/plot_provenance_audit.py',
        'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],
        'matplotlib':matplotlib.__version__,
        'scope':'Only acquired artifact identities. No malware or obfuscation prevalence inference.'},indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
