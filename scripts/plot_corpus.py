"""Regenerate descriptive figures; structural markers are not obfuscation labels."""
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'data/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from analyze_corpus import ROOT, OUT

FIG=OUT/'figures'


def read(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def save(fig,name):
    for ext in ['png','svg','pdf']:
        fig.savefig(FIG/(name+'.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)


def main():
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    occurrences=read('occurrence-manifest.csv')
    datasets=['wasmmal','wasmbench','wasmixer','minerray','swamped','diversification2022']
    labels=['WasmMal','WasmBench filtered','WASMixer','MinerRay','SWAMPED','Diversification']
    sets={d:{r['sha256'] for r in occurrences if r['dataset']==d} for d in datasets}
    counts=[sum(r['dataset']==d for r in occurrences) for d in datasets]
    fig,ax=plt.subplots(figsize=(10,4.6))
    x=np.arange(len(datasets)); width=.37
    ax.bar(x-width/2,counts,width,label='File occurrences',color='#64748b')
    ax.bar(x+width/2,[len(sets[d]) for d in datasets],width,label='Unique SHA-256',color='#2563eb')
    for i,d in enumerate(datasets):
        ax.text(i-width/2,counts[i]*1.10,f'{counts[i]:,}',ha='center',fontsize=8)
        ax.text(i+width/2,len(sets[d])*1.10,f'{len(sets[d]):,}',ha='center',fontsize=8)
    ax.set_yscale('log'); ax.set_ylim(1,100000)
    ax.set_xticks(x,labels,rotation=18,ha='right'); ax.set_ylabel('Count (log scale)')
    ax.set_title('Acquired corpus snapshot: occurrences and byte-distinct modules')
    ax.legend(frameon=False,loc='upper right')
    fig.subplots_adjust(bottom=.27)
    fig.text(.02,.005,'2026-10-06 snapshot; computed member hashes only. Repository and release scope differs by corpus.',fontsize=9)
    save(fig,'01-corpus-composition')

    matrix=np.array([[len(sets[a]&sets[b]) for b in datasets] for a in datasets])
    fig,ax=plt.subplots(figsize=(8.5,6.5))
    im=ax.imshow(np.log10(matrix+1),cmap='Blues')
    for i in range(len(datasets)):
        for j in range(len(datasets)):
            ax.text(j,i,f'{matrix[i,j]:,}',ha='center',va='center',color='white' if matrix[i,j]>1000 else '#111827')
    ax.set_xticks(range(len(datasets)),labels,rotation=30,ha='right')
    ax.set_yticks(range(len(datasets)),labels)
    ax.set_title('Shared SHA-256 identities across acquired corpora')
    fig.colorbar(im,ax=ax,shrink=.7,label='log10(shared count + 1)')
    fig.subplots_adjust(bottom=.26)
    fig.text(.02,.005,'Diagonal: distinct modules. Equal bytes do not establish malware intent or independent provenance.',fontsize=9)
    save(fig,'02-corpus-overlap')

    cohorts={r['cohort']:r for r in read('cohort-summary.csv')}
    names=['swamped/Cryptojackers_43','swamped/Malware_31','wasm-obf/binaries/unobfuscated','wasm-obf/binaries/tigress']
    text=['SWAMPED\ncryptojacker seeds','SWAMPED\nmalware seeds','Cryptic Bytes\nunobfuscated','Cryptic Bytes\nTigress variants']
    fig,ax=plt.subplots(figsize=(9.3,4.9)); x=np.arange(len(names)); width=.35
    for offset,key,label,color in [(-width/2,'br_table_count_present','Any br_table','#2563eb'),(width/2,'br_table_in_loop_count_present','br_table inside a loop','#d97706')]:
        values=[]
        for name in names:
            row=cohorts[name]; values.append(100*int(row[key])/int(row['analyzed_ok']))
        ax.bar(x+offset,values,width,label=label,color=color)
        for i,name in enumerate(names):
            row=cohorts[name]
            ax.text(i+offset,values[i]+1.5,f"{row[key]}/{row['analyzed_ok']}",ha='center',fontsize=9)
    ax.set_xticks(x,[f'{label}\nAnalyzed {cohorts[name]["analyzed_ok"]}/{cohorts[name]["unique_sha256"]}' for label,name in zip(text,names)])
    ax.set_ylim(0,130); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel('Share of analyzed distinct modules (%)')
    ax.set_title('Structural markers are common in seeds and generated variants')
    ax.legend(frameon=False,loc='upper right',ncol=2)
    fig.subplots_adjust(bottom=.27)
    fig.text(.02,.005,'Markers are not obfuscation verdicts. Cryptic Bytes includes generated research variants; not a prevalence sample.',fontsize=9)
    save(fig,'03-structural-marker-limitations')
    inputs={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['occurrence-manifest.csv','cohort-summary.csv']}
    metadata={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'matplotlib':matplotlib.__version__,'numpy':np.__version__,'inputs_sha256':inputs,
              'scope':'fixed public-corpus snapshot analyzed on 2026-10-06; markers are descriptive, not obfuscation verdicts'}
    (FIG/'generation.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata))


if __name__=='__main__': main()
