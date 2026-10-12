"""Plot measured byte identity of paired WASMixer public artifact files."""
import hashlib
import json
import os
from acquire import ROOT
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    source=ROOT/'results/controls/wasmixer-pair-summary.json'
    data=[r for r in json.loads(source.read_text()) if r['group']=='basic-algorithms']
    labels=[r['declared_transform'] for r in data]
    equal=[r['exact_bytes_equal_pairs'] for r in data]
    different=[r['paired_paths']-r['exact_bytes_equal_pairs'] for r in data]
    fig,ax=plt.subplots(figsize=(8.4,4.5),layout='constrained')
    ax.barh(labels,equal,color='#246b8e',label='Identical bytes to paired origin')
    ax.barh(labels,different,left=equal,color='#d8e1e8',label='Different bytes (not proof of transformation)')
    ax.invert_yaxis();ax.set_xlim(0,108)
    ax.set_xlabel('Same-name file pairs (101 per author directory)')
    ax.set_title('Author directory names do not establish transformed controls',loc='left',fontsize=13)
    ax.set_xticks([0,25,50,75,101]);ax.spines[['top','right']].set_visible(False)
    for i,n in enumerate(equal):
        ax.text(2,i,f'{n}/101 byte-identical',va='center',color='white' if n else '#243b4a',fontsize=10)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),frameon=False,fontsize=8)
    fig.suptitle('WASMixer basic-algorithms, pinned commit 9cc0cf2; acquired bytes rehashed',fontsize=9,color='#555555')
    output=ROOT/'results/controls/figures';output.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg','pdf']:
        fig.savefig(output/('control-label-audit.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    (output/'generation.json').write_text(json.dumps({'script':'scripts/plot_control_audit.py',
        'input':source.relative_to(ROOT).as_posix(),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'matplotlib':matplotlib.__version__,'scope':'byte-identity audit of this artifact version; no malware prevalence or whole-paper assessment'},indent=2),encoding='utf-8')


if __name__=='__main__':main()
