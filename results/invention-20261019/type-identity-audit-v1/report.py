import argparse,json,statistics
from pathlib import Path
import prototype as q
def main(main,perf,out):
    main,perf,out=map(Path,(main,perf,out));out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((perf/'summary.json').read_text());manifest=json.loads((main/'manifest.json').read_text());text=['# 型同値状態の測定比較','', 'nsは1回のrun(x,31)。各条件3 fresh process、10,000回warmup後に10,000回×9標本。process内中央値の中央値。ホストloopを含む。readは外部wasm-disの起動・正規化・AST parseを含む。lowerはその後のPython変換。両時間の比を保護強度と呼ばない。','','|kernel|mode|groups|siblings|opt|bytes|run ns|process中央値の範囲 ns|read ms|lower ms|compile ms|RSS KiB|','|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in rows:
        v=x['process_medians_ns'];text.append(f"|{x['kernel']}|{x['mode']}|{x['groups']}|{x['siblings']}|{x['opt']}|{x['bytes']}|{x['ns']:.2f}|{min(v):.2f}–{max(v):.2f}|{x['read_ms']:.3f}|{x['lower_ms']:.3f}|{x['compile_ms']:.3f}|{x['peak_rss_kib']:.0f}|")
    ratios=[]
    for x in rows:
        if x['mode']!='groups' or x['groups']!=8 or x['siblings']!=32:continue
        base=next(y for y in rows if y['kernel']==x['kernel'] and y['opt']==x['opt'] and y['mode']=='gc')
        ratios.append(dict(kernel=x['kernel'],opt=x['opt'],runtime=x['ns']/base['ns'],read=x['read_ms']/base['read_ms'],lower=x['lower_ms']/base['lower_ms'],bytes=x['bytes']/base['bytes']))
    same=[]
    for x in manifest:
        if x['mode']!='groups':continue
        b=next(y for y in manifest if y['kernel']==x['kernel'] and y['opt']==x['opt'] and y['mode']=='gc')
        same.append(dict(file=x['file'],same_recovered_bytes=x['recovered_sha256']==b['recovered_sha256']))
    q.save(out/'ratios.json',ratios);q.save(out/'recovered-identity.json',same)
    q.save(out/'summary.json',dict(gc_targets=sum(x['mode'] in ('gc','groups') for x in manifest),same_recovered_as_gc=sum(x['same_recovered_bytes'] for x in same),group_conditions=len(same),fresh_processes=len(rows)*3,ratios={k:[min(x[k] for x in ratios),max(x[k] for x in ratios)] for k in ('runtime','read','lower','bytes')},transform_ms_range=[min(x['transform_ms'] for x in manifest),max(x['transform_ms'] for x in manifest)],peak_rss_kib_range=[min(x['peak_rss_kib'] for x in rows),max(x['peak_rss_kib'] for x in rows)]))
    (out/'comparison.md').write_text('\n'.join(text)+'\n',encoding='utf-8');print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('main');a.add_argument('performance');a.add_argument('output');v=a.parse_args();main(v.main,v.performance,v.output)
