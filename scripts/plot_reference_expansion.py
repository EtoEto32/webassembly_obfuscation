"""Plot sensitivity to adding four independently located reference modules."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'results/sensitivity-minesweeper/reference-expansion-comparison.json'
    rows=json.loads(source.read_text(encoding='utf-8'))['loop_marker_comparison']
    fig,(left,right)=plt.subplots(1,2,figsize=(11.6,5.2))
    fig.subplots_adjust(left=.08,right=.98,bottom=.25,top=.82,wspace=.28)
    selected=[r for r in rows if r['tie_rule']=='lex_first'];x=list(range(len(selected)))
    for column,label,color in [('old','56 usable references','#708ba5'),('new','60 usable references','#b55d30')]:
        left.plot(x,[r[column+'_groups'] for r in selected],marker='o',color=color,label=label)
    left.set(title='A. Number of modeled groups',ylabel='Groups (not verified families)')
    left.legend(frameon=False,fontsize=9)
    for rule,style in [('lex_first','-'),('ambiguous_singleton','--')]:
        selected=[r for r in rows if r['tie_rule']==rule]
        for column,n,color in [('old',56,'#708ba5'),('new',60,'#b55d30')]:
            label=f'{n} refs / '+('assign ties' if rule=='lex_first' else 'keep ambiguous singletons')
            right.plot(x,[100*r[column+'_loop_marker_group_mean'] for r in selected],
                       style,marker='o',color=color,label=label)
    raw=100*rows[0]['old_loop_marker_group_mean']
    right.axhline(raw,color='#555555',lw=1,linestyle=':',label=f'SHA-only: {raw:.2f}%')
    right.set(title='B. Loop/br_table structural marker',ylabel='Equal-group mean (%)',ylim=(10,57))
    right.legend(frameon=False,fontsize=8,loc='lower right')
    for ax in (left,right):
        ax.set_xticks(x,labels=['0.80','0.90','0.95','0.99','1.00'])
        ax.set_xlabel('Exact-function-body weighted Jaccard threshold')
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18)
        ax.title.set_fontsize(11)
    fig.suptitle('Reference coverage changes similarity-based summaries',fontsize=14)
    fig.text(.08,.06,'Same 7,510 successfully analyzed WasmMal author-malware binaries in every model.\n'
             'Four MineSweeper matches add usable references; raw module measurements are unchanged.\n'
             'Structural markers and modeled groups do not estimate obfuscation prevalence or malware families.',
             fontsize=9,color='#444444',linespacing=1.45)
    output=ROOT/'results/sensitivity-minesweeper/figures';output.mkdir(exist_ok=True)
    for ext in ('png','svg','pdf'):
        fig.savefig(output/('reference-expansion.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    (output/'generation.json').write_text(json.dumps({'script':'scripts/plot_reference_expansion.py',
        'matplotlib':matplotlib.__version__,'input':source.relative_to(ROOT).as_posix(),
        'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2),encoding='utf-8')


if __name__=='__main__':main()
