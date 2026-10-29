"""Plot audited pilot ratios, preserving the two repetitions as individual points."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'results/followup-evaluation-20261016/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();audit_path=run/'pilot-audit.json'
    data=json.loads(audit_path.read_text(encoding='utf-8'));assert data['status'] in ['passed','measurement-checks-passed-with-compiler-mode-deviation']
    out=ROOT/'results/followup-evaluation-20261016/figures';out.mkdir(exist_ok=True)
    font_manager.fontManager.addfont('C:/Windows/Fonts/meiryo.ttc')
    plt.rcParams['font.family']=font_manager.FontProperties(fname='C:/Windows/Fonts/meiryo.ttc').get_name()
    plt.rcParams['font.size']=10
    modes=['default','liftoff','turbofan'];mode_labels=['通常設定','Liftoff指定\n実際は混在','TurboFan固定']
    styles=[('swamped',[('nop10','NOP挿入'),('constsplit10','整数定数分割')]),
            ('xmr-wasm',[('xmr-wasm-emccobf-flattening','平坦化'),('xmr-wasm-emccobf-substitution','命令置換')])]
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for ax,(family,methods) in zip(axes,styles):
        for mi,(identifier,label) in enumerate(methods):
            rows=[r for r in data['bracket_comparisons'] if r['artifact_id']==identifier]
            color=['#0072B2','#D55E00'][mi]
            for repetition in [1,2]:
                selected=[next(r for r in rows if r['mode']==mode and r['repetition']==repetition) for mode in modes]
                x=[i+(mi-.5)*.16+(repetition-1.5)*.035 for i in range(3)]
                ax.scatter(x,[r['ratio'] for r in selected],color=color,marker=['o','s'][repetition-1],s=36,
                    label=label if repetition==1 else None)
        ax.axhline(1,color='#555555',ls='--',lw=1)
        ax.set_xticks(range(3),mode_labels);ax.set_title('SWAMPED由来' if family=='swamped' else 'xmr-wasm配布物')
        ax.set_xlabel('コンパイル設定');ax.set_ylabel('近接した基準測定に対する速度の比')
        upper=max(1,max(r['ratio'] for r in data['bracket_comparisons'] if r['family']==family))*1.10
        ax.set_ylim(0,upper);ax.grid(axis='y',alpha=.25);ax.legend()
    fig.suptitle('JIT条件別の速度比較　各点は1巡回の比')
    fig.savefig(out/'pilot-bracket-ratios.png',dpi=180);fig.savefig(out/'pilot-bracket-ratios.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.3),layout='constrained')
    for fi,family in enumerate(['swamped','xmr-wasm']):
        rows=[r for r in data['AA_comparisons'] if r['family']==family]
        for repetition in [1,2]:
            selected=[next(r for r in rows if r['mode']==mode and r['repetition']==repetition) for mode in modes]
            x=[i+(fi-.5)*.16+(repetition-1.5)*.035 for i in range(3)]
            ax.scatter(x,[r['ratio'] for r in selected],label=family if repetition==1 else None,
                color=['#009E73','#CC79A7'][fi],marker=['o','s'][repetition-1],s=40)
    ax.axhline(1,color='#555555',ls='--',lw=1);ax.set_xticks(range(3),mode_labels)
    ax.set_ylabel('同じ基準版の2回目／1回目の速度');ax.set_xlabel('コンパイル設定')
    ax.set_title('同じバイナリ同士の比較で生じる変動');ax.legend();ax.grid(axis='y',alpha=.25)
    fig.savefig(out/'pilot-AA-ratios.png',dpi=180);fig.savefig(out/'pilot-AA-ratios.svg');plt.close(fig)
    metadata=dict(audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        plot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        note='Pilot: two repetitions per variant and mode. Points are not confidence intervals. Sequential interpolation does not remove arbitrary interference.',
        files=['pilot-bracket-ratios.png','pilot-bracket-ratios.svg','pilot-AA-ratios.png','pilot-AA-ratios.svg'])
    (out/'pilot-generation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(str(out))


if __name__=='__main__':
    main()
