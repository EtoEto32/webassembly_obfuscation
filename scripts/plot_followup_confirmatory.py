"""Render only completed/audited confirmatory measurements; no provisional values."""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt


GROUPS=[('swamped-controlled','SWAMPED', [('swamped-nop','NOP'),('swamped-constsplit','定数分割')]),
    ('xmr-wasm-controlled','xmr-wasm', [('xmr-wasm-nop','NOP'),('xmr-wasm-constsplit','定数分割')]),
    ('webminerpoolhashcn-controlled','webminerpoolhashcn', [('webminerpoolhashcn-nop','NOP'),('webminerpoolhashcn-constsplit','定数分割')]),
    ('xmr-helper-ablation','平坦化版の部位復元', [('restore-xor8','8バイトXOR'),('restore-xor16','16バイトXOR'),('restore-both','両方')])]
COLORS=['#0072B2','#D55E00']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary_path=OUT/'confirmatory-summary.json';structure_path=OUT/'confirmatory-structure.json'
    summary=json.loads(summary_path.read_text(encoding='utf-8'))
    structure=json.loads(structure_path.read_text(encoding='utf-8'))
    assert summary['status']=='all-three-sessions-audited' and summary['timed_blocks']==272
    assert len(summary['sources'])==3 and len(summary['summaries'])==18
    assert structure['status']=='wabt-static-analysis-passed'
    font_manager.fontManager.addfont('C:/Windows/Fonts/meiryo.ttc')
    plt.rcParams['font.family']=font_manager.FontProperties(fname='C:/Windows/Fonts/meiryo.ttc').get_name()
    plt.rcParams['font.size']=10
    out=OUT/'figures';out.mkdir(exist_ok=True);files=[]
    def save(fig,name):
        for extension in ['png','svg']:
            path=out/(name+'.'+extension)
            if path.exists():raise RuntimeError('Preserve existing figure: '+str(path))
            fig.savefig(path,dpi=180);files.append(dict(path=path.name,sha256=sha(path)))
        plt.close(fig)
    rows={(r['mode'],r['group'],r['artifact_id']):r for r in summary['summaries']}
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,(group,title,variants) in zip(axes.flat,GROUPS):
        for mi,mode in enumerate(['liftoff','turbofan']):
            for index,(identifier,label) in enumerate(variants):
                row=rows[mode,group,identifier];center=index+(mi-.5)*.28
                values=row['ratios_by_repetition'];assert len(values)==6
                ax.scatter([center+(i-2.5)*.017 for i in range(6)],values,s=18,color=COLORS[mi],alpha=.65)
                lo,hi=row['exploratory_session_t_interval_95'];mean=row['geometric_mean_ratio']
                ax.errorbar(center,mean,yerr=[[mean-lo],[hi-mean]],fmt='D',ms=6,capsize=4,
                    color=COLORS[mi],label=['Liftoff単独','TurboFan単独'][mi] if index==0 else None)
        ax.axhline(1,color='#555555',ls='--',lw=1);ax.set_title(title)
        ax.set_xticks(range(len(variants)),[v[1] for v in variants]);ax.grid(axis='y',alpha=.25)
        ax.set_ylabel('近接基準に対する速度比');ax.legend(fontsize=9)
        ax.set_ylim(bottom=0)
    fig.suptitle('難読化・部位復元の速度比較\n点：6巡回　菱形：幾何平均　棒：3セッションによる探索的な個別95%区間',fontsize=12)
    save(fig,'confirmatory-speed-ratios')
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,mode,mode_label in zip(axes,['liftoff','turbofan'],['Liftoff単独','TurboFan単独']):
        for gi,(group,title,variants) in enumerate(GROUPS):
            for vi,(identifier,label) in enumerate(variants):
                structural=next(r for r in structure['comparisons'] if r['group']==group and r['artifact_id']==identifier)
                runtime=rows[mode,group,identifier]
                ax.scatter(structural['instruction_ratio'],runtime['geometric_mean_ratio'],s=40,
                    marker=['o','s','^','D'][gi],color=['#0072B2','#D55E00','#009E73'][vi],
                    label=title+' '+label)
        ax.axhline(1,color='#777777',ls='--',lw=1);ax.axvline(1,color='#777777',ls='--',lw=1)
        ax.set_xlabel('保存された命令数の比');ax.set_ylabel('近接基準に対する速度比');ax.set_title(mode_label)
        ax.grid(alpha=.2)
    axes[1].legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8)
    fig.suptitle('同じバイナリの構造と性能\n部位復元の基準は平坦化版、その他の基準は各実装の未変換版',fontsize=12)
    save(fig,'confirmatory-structure-speed')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    pairs=summary['baseline_reference_pairs'];assert len(pairs)==108
    for ax,mode,mode_label in zip(axes,['liftoff','turbofan'],['Liftoff単独','TurboFan単独']):
        for gi,(group,title,variants) in enumerate(GROUPS):
            for session in [1,2,3]:
                selected=[p for p in pairs if p['mode']==mode and p['group']==group and p['session']==session]
                ax.scatter([gi+(i-(len(selected)-1)/2)*.035 for i in range(len(selected))],
                    [p['right_over_left'] for p in selected],s=22,alpha=.65,
                    color=['#0072B2','#D55E00','#009E73'][session-1],label='セッション'+str(session) if gi==0 else None)
            checks=[p for p in summary['AA_comparisons'] if p['mode']==mode and p['group']==group]
            for p in checks:
                ax.scatter(gi,p['ratio'],s=80,marker='*',facecolors='none',edgecolors='#222222',
                    label='連続したA/A' if gi==0 else None)
        ax.axhline(1,color='#555555',ls='--',lw=1)
        ax.set_xticks(range(4),['SWAMPED','xmr-wasm','webminerpool','部位復元'],rotation=12)
        ax.set_ylabel('同じ基準版の後／前の速度比');ax.set_title(mode_label);ax.grid(axis='y',alpha=.25)
    axes[1].legend(fontsize=9)
    fig.suptitle('基準版同士で観測された変動\n近接基準は隣の比較と共有され得るため、独立標本として扱わない',fontsize=12)
    save(fig,'confirmatory-baseline-variation')
    result=dict(summary_sha256=sha(summary_path),structure_sha256=sha(structure_path),
        plot_script_sha256=sha(Path(__file__)),files=files,
        note='All 18 planned contrasts. Pointwise unadjusted intervals use three consecutive session means and are exploratory; no simultaneous-coverage, confirmatory-significance, equivalence or population inference. Static instructions are not dynamic execution counts.',
        visual_review='pending; inspect both rendered PNGs before final delivery')
    (out/'confirmatory-generation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
