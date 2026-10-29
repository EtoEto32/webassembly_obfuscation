"""Plot the fixed-denominator matching outcomes, including unavailable provenance."""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/followup-evaluation-20261016'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=OUT/'normalization-matching-results.json';data=json.loads(source.read_text(encoding='utf-8'))
    assert data['status']=='all-frozen-matching-queries-scored' and len(data['function_records'])==4508
    font_manager.fontManager.addfont('C:/Windows/Fonts/meiryo.ttc')
    plt.rcParams['font.family']=font_manager.FontProperties(fname='C:/Windows/Fonts/meiryo.ttc').get_name()
    plt.rcParams['font.size']=10
    out=OUT/'figures';out.mkdir(exist_ok=True);files=[]
    rows=data['summaries'];labels=['未処理','NOP除去','整数定数畳み込み','両規則','Binaryen 局所pass','Binaryen O2','Binaryen O3']
    styles=[('correct_unique','正しい一意照合','#009E73'),('ambiguous_with_correct','正解を含む複数候補','#56B4E9'),
        ('unmatched','未照合','#BFC3C7'),('query_origin_not_retained','由来を追跡できない','#E69F00'),
        ('wrong_unique','誤った一意照合','#D55E00'),('ambiguous_without_correct','正解を含まない複数候補','#CC79A7'),
        ('query_origin_ambiguous','由来の追跡が複数候補','#F0E442')]
    def save(fig,name):
        for extension in ['png','svg']:
            path=out/(name+'.'+extension);assert not path.exists()
            fig.savefig(path,dpi=180,bbox_inches='tight');files.append(dict(path=path.name,sha256=sha(path)))
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,6),layout='constrained');left=[0]*7
    for key,label,color in styles:
        values=[r['outcomes'].get(key,0) for r in rows]
        if not any(values):continue
        ax.barh(range(7),values,left=left,color=color,label=label,height=.68)
        for i,value in enumerate(values):
            if value>=18:ax.text(left[i]+value/2,i,str(value),ha='center',va='center',fontsize=9)
        left=[a+b for a,b in zip(left,values)]
    assert left==[644]*7
    ax.set_yticks(range(7),labels);ax.invert_yaxis();ax.set_xlim(0,644)
    ax.set_xlabel('入力時点の対象関数644件／処理（由来を追跡できない関数も含む）')
    ax.set_title('関数対応付け：構文指紋の完全一致\n既知由来の有限事例。名前・関数番号は照合特徴に使わない。',pad=12)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,fontsize=9);ax.grid(axis='x',alpha=.2)
    save(fig,'normalization-function-matching')
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained');correct=[r['module_outcomes'].get('correct_unique',0) for r in rows]
    assert all(sum(r['module_outcomes'].values())==8 for r in rows)
    assert all(set(r['module_outcomes'])<={'correct_unique','unmatched'} for r in rows)
    ax.barh(range(7),correct,color='#009E73',label='正しい一意照合',height=.68)
    ax.barh(range(7),[8-v for v in correct],left=correct,color='#BFC3C7',label='未照合',height=.68)
    for i,value in enumerate(correct):
        ax.text(max(value/2,.12),i,str(value),ha='center',va='center',fontsize=10)
    ax.set_yticks(range(7),labels);ax.invert_yaxis();ax.set_xlim(0,8);ax.set_xticks(range(9))
    ax.set_xlabel('問い合わせ8件／処理（生成対照6件・公開複雑版2件）')
    ax.set_title('モジュール全体の照合：標準WATの完全一致\n同じ処理をした基準3件から照合。意味同値性や検知精度は評価しない。',pad=12)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,fontsize=9);ax.grid(axis='x',alpha=.2)
    save(fig,'normalization-module-matching')
    manifest=dict(source_sha256=sha(source),plot_script_sha256=sha(Path(__file__)),files=files,
        scope='All 4508 function queries and 56 module queries. Fixed denominators; correlated known-lineage examples, no confidence intervals or population inference.',visual_review='pending')
    target=out/'normalization-generation.json';assert not target.exists();target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
