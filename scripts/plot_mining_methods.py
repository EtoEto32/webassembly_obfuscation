# -*- coding: utf-8 -*-

"""Japanese vector figures from frozen source-program method statistics."""

import csv

import json

import os

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/matplotlib-cache'))

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from matplotlib import font_manager



OUT=ROOT/'results/mining-methods'

LABELS={

 'llvm/bcfobf':'LLVM：偽の制御フローの追加', 'llvm/cffobf':'LLVM：制御フロー平坦化',

 'llvm/constenc':'LLVM：定数の難読化','llvm/funcwra':'LLVM：ラッパー関数の追加',

 'llvm/indibran':'LLVM：間接分岐','llvm/splitobf':'LLVM：基本ブロック分割',

 'llvm/strcry':'LLVM：文字列の暗号化','llvm/subobf':'LLVM：命令置換',

 'tigress/antialiasanalysis':'Tigress：エイリアス解析への対策',

 'tigress/antitaintanalysis':'Tigress：テイント解析への対策',

 'tigress/encodearithmetic':'Tigress：算術式の難読化',

 'tigress/encodeliterals':'Tigress：整数定数・文字列の難読化',

 'tigress/flatten':'Tigress：制御フロー平坦化',

 'tigress/randomfuns':'Tigress：ランダムな関数の生成',

 'tigress/split':'Tigress：関数分割','tigress/virtualize':'Tigress：コードの仮想化',

 'wasm-mutate/iteration-series':'wasm-mutate：複数手法の繰り返し適用'}





def main():

    font=Path('C:/Windows/Fonts/meiryo.ttc')

    font_manager.fontManager.addfont(str(font))

    plt.rcParams.update({'font.family':'Meiryo','font.size':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.unicode_minus':False})

    rows=list(csv.DictReader((OUT/'method-summary.csv').open(encoding='utf-8')))

    methods=list(LABELS)

    fig,axs=plt.subplots(1,2,figsize=(7.1,5.1),sharey=True)

    for ax,metric,title in zip(axs,('instruction_count','bytes'),('命令数','ファイルサイズ')):

        for release,offset,color,label in [('binaries',-.15,'#155b8d','未最適化版'),('binaries-opt',.15,'#ad4d14','最適化済み版')]:

            for i,m in enumerate(methods):

                r=next(r for r in rows if r['release']==release and r['method']==m and r['metric']==metric and r['statistic']=='ratio')

                low,q1,med,q3,high=[float(r[k]) for k in ('minimum','q1','median','q3','maximum')]

                y=i+offset

                ax.plot([low,high],[y,y],color=color,lw=.7)

                ax.plot([q1,q3],[y,y],color=color,lw=3)

                ax.plot(med,y,'o',ms=3,color=color,label=label if i==0 else None)

        ax.axvline(1,color='gray',ls='--',lw=.7)

        ax.set_title(title);ax.set_xlabel('同じ最適化条件の基準版に対する比')

        ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False)

    axs[0].set_yticks(range(len(methods)),[LABELS[m] for m in methods]);axs[0].invert_yaxis()

    axs[1].legend(loc='lower right',fontsize=7)

    fig.subplots_adjust(left=.35,right=.98,bottom=.19,top=.94,wspace=.15)

    fig.text(.35,.035,'対象：採掘用プログラム10本（同系列の派生版を含む）\n点：中央値　太線：中央50%の範囲　細線：最小値～最大値\n元のプログラムごとに変換後のバイナリの中央値を求めてから集計',fontsize=7)

    folder=OUT/'figures';folder.mkdir(exist_ok=True)

    for ext in ('pdf','svg','png'):fig.savefig(folder/f'method-size-instructions.{ext}',dpi=180)

    plt.close(fig)

    (OUT/'figure-settings.json').write_text(json.dumps(dict(font=str(font),labels=LABELS,

       input='method-summary.csv',width_inches=7.1,height_inches=5.1,

       limitation='Japanese technique labels translate declared settings; not per-binary confirmation'),ensure_ascii=False,indent=2),encoding='utf-8')

    print(folder/'method-size-instructions.pdf')





if __name__=='__main__':main()

