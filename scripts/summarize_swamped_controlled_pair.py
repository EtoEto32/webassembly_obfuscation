"""Summarize only completed finite-vector-validated controlled hashing measurements."""
import csv
import hashlib
import json
import os
import statistics
from pathlib import Path
from analyze_corpus import analyze

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset/swamped'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/matplotlib-cache'))

def main():
    report=json.loads((OUT/'controlled-pair-repeated-throughput.json').read_text())
    assert report.get('status')=='complete' and report.get('finished_utc')
    assert len(report['samples'])==9
    manifest=(OUT/'controlled-pair-manifest.json').read_bytes()
    assert hashlib.sha256(manifest).hexdigest()==report['manifest_sha256']
    spec=json.loads(manifest)
    rows=[];static=[]
    for case in spec['cases']:
        result=analyze(case)
        assert result['status']=='ok' and result['valid_wabt']
        static.append(result)
        (OUT/(case['name']+'-static.json')).write_text(json.dumps(result)+'\n')
        samples=[s for s in report['samples'] if s['sha256']==case['sha256']]
        assert sorted(s['repetition'] for s in samples)==[1,2,3]
        assert all(s['final_output_matches'] and all(v['matches'] for v in s['post_block_checks']) for s in samples)
        rates=[s['hashes_per_second'] for s in samples]
        tags=[x for f in case['changes'] for x in f['changes']]
        rows.append(dict(name=case['name'],sha256=case['sha256'],median_hps=statistics.median(rates),
                         min_hps=min(rates),max_hps=max(rates),bytes=result['bytes'],
                         instructions=result['instruction_count'],transformed_functions=case['transformed_functions'],
                         transformation_sites=(len(tags)//3 if case['source_function']=='constant_value_splitting' else len(tags)),
                         correct_public_vectors=5,repetitions=3,seconds_per_block=30))
    assert all(r['imports']==static[0]['imports'] and r['exports']==static[0]['exports'] for r in static)
    assert rows[0]['sha256']==spec['original_sha256'],'Roundtrip changed original bytes'
    for row in rows:
        row['throughput_ratio']=row['median_hps']/rows[0]['median_hps']
        row['size_ratio']=row['bytes']/rows[0]['bytes']
        row['instruction_ratio']=row['instructions']/rows[0]['instructions']
    with (OUT/'controlled-pair-summary.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'controlled-pair-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(8,3.2),layout='constrained')
    labels=['Reference','NOP insertion','Integer constant splitting']
    med=[r['median_hps'] for r in rows]
    axes[0].bar(range(3),med,color='#4477AA')
    axes[0].errorbar(range(3),med,yerr=[[r['median_hps']-r['min_hps'] for r in rows],
                                    [r['max_hps']-r['median_hps'] for r in rows]],fmt='none',color='black',capsize=3)
    axes[0].set_ylabel('Hashes/s: median and min/max (3 runs)')
    for key,label,marker in [('size_ratio','File size','o'),('instruction_ratio','Instructions','s'),('throughput_ratio','Hash throughput','^')]:
        axes[1].plot(range(3),[r[key] for r in rows],marker+'-',label=label)
    axes[1].axhline(1,color='grey',lw=.7);axes[1].set_ylabel('Ratio to same-assembly reference');axes[1].legend(fontsize=8)
    for ax in axes:ax.set_xticks(range(3),labels,rotation=15,ha='right',fontsize=8)
    fig.savefig(OUT/'controlled-pair-throughput.pdf');fig.savefig(OUT/'controlled-pair-throughput.png',dpi=160)
    plt.close(fig)
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
