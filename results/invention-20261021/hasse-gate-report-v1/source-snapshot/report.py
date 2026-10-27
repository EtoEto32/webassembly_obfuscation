import argparse
import json
import shutil
import statistics
from pathlib import Path
import prototype as p


def run(main,runtime,audit,out):
    main,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,runtime,audit,out))
    out.mkdir(parents=True,exist_ok=False)
    m=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    rt=json.loads((runtime/'runtime.json').read_text(encoding='utf-8'))
    checks=json.loads((main/'checks.json').read_text(encoding='utf-8'))
    au=json.loads((audit/'audit.json').read_text(encoding='utf-8'))
    for folder,pinsfile,pinkey in [(main,'pins.json',None),(runtime,'protocol.json','pins')]:
        pins=json.loads((folder/pinsfile).read_text(encoding='utf-8'))
        if pinkey:pins=pins[pinkey]
        assert all(p.q.digest(folder/name)==digest for name,digest in pins.items())
    rows=[]
    for case in m['cases']:
        name=case['name']; measures={}
        for mode in ('source','jet','recovered'):
            values=[r['measurement']['medianNs'] for r in rt if r['name']==name and r['mode']==mode]
            measures[mode]=dict(median_ns=statistics.median(values),process_medians_ns=values,range_ns=[min(values),max(values)])
        s,j=[next(r for r in m['targets'] if r['name']==name and r['opt']=='O3' and r['mode']==mode) for mode in ('source','jet')]
        row=dict(name=name,order=case['order'],degree=case['transform']['degree'],transform_ms=case['transform']['transform_ms'],
                 performance=measures,bytes={'source':s['bytes'],'jet':j['bytes'],'recovered':(main/j['recovered']).stat().st_size},
                 analysis={mode:dict(read_ms=r['recovery']['read_ms'],normalize_median_ms=statistics.median(r['recovery']['normalize_samples_ms']),terms=r['recovery']['terms'],
                               coefficient_products=r['recovery']['coefficient_products']) for mode,r in [('source',s),('jet',j)]})
        rows.append(row)
    p.q.save(out/'report.json',dict(rows=rows,calls=checks['calls'],control_calls=checks['controls']['calls'],byte_replays=au['byte_replays'],interpreter_probes=au['interpreter_probes'],
          status_counts={status:sum(t['status']==status for t in m['targets']) for status in ('recovered','unsupported','crash','timeout','failed')},
          rss_kib_range=[min(r['measurement']['maxRssKiB'] for r in rt),max(r['measurement']['maxRssKiB'] for r in rt)]))
    lines=['# Hasse係数変換の測定値','','O3。時間は3 fresh processの各9 batch中央値の中央値。ns/呼出しは共通Wasm loopを含む。',
           '解析はWABT読取1回と、同一Python process内の正規化11反復を分離した。人間の実装時間は含めない。','',
           '|式 (d,k)|source ns|jet ns|Horner回復 ns|jet/source|source/jet bytes|source/jet正規化 ms|source/jet読取 ms|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        s,j,h=[row['performance'][mode]['median_ns'] for mode in ('source','jet','recovered')]
        a,b=row['analysis']['source'],row['analysis']['jet']
        lines.append(f"|{row['name']} ({row['degree']},{row['order']})|{s:.3f}|{j:.3f}|{h:.3f}|{j/s:.3f}|{row['bytes']['source']}/{row['bytes']['jet']}|{a['normalize_median_ms']:.4f}/{b['normalize_median_ms']:.4f}|{a['read_ms']:.3f}/{b['read_ms']:.3f}|")
    lines+=['','Horner回復は係数表からの等価実装であり、元の因数分解やDAGを回復したとはいわない。',
            '今回の回復版は全4例でjet版より遅い。係数の回復と高速な複製は別の課題である。',
            '正規化本体は約1.6–32.8倍に増えた。この増分を無視しないが、既知の係数算術と差が弱く、独立した主発明には不採用。',
            '単一CPU/V8、4合成式のみ。実アプリの保護・特許性・一般的な解析困難性は未確立。','']
    (out/'comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    snapshot=out/'source-snapshot';snapshot.mkdir()
    for f in Path(__file__).parent.iterdir():
        if f.is_file():shutil.copy2(f,snapshot/f.name)
    p.q.save(out/'input-pins.json',{str(f.relative_to(p.ROOT)):p.q.digest(f) for folder in (main,runtime,audit) for f in folder.rglob('*') if f.is_file()})
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({'rows':len(rows),'output':str(out)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('runtime');ap.add_argument('audit');ap.add_argument('output');a=ap.parse_args();run(a.main,a.runtime,a.audit,a.output)
