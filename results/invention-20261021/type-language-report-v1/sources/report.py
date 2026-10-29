"""Collect bounded experiment evidence and pin the sources used for reproduction."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import statistics

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/invention-20261021'
HERE=Path(__file__).resolve().parent


def read(f):return json.loads(f.read_text(encoding='utf-8'))
def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    directories={'regular':BASE/'type-language-wasm-v2','forced':BASE/'type-language-forced-v1'}
    measure=BASE/'type-language-measure-v1'
    runtime=read(measure/'runtime.json');shapes=read(measure/'shape-recovery.json')
    summary={'scope':'known peeling control and type-recovery gate; goal not achieved',
             'correctness':{},'solver_status':{},'runtime':[],'shape_recovered':len(shapes),
             'shape_ms_range':[min(x['shape_ms_median'] for x in shapes),max(x['shape_ms_median'] for x in shapes)],
             'reader_ms_range':[min(x['reader_ms'] for x in shapes),max(x['reader_ms'] for x in shapes)],
             'replayed_binaries':len(read(measure/'replay.json'))}
    lines=['# 型回復の対照実験','',
           'O3、3 fresh Node processの中央値。各processは32768呼出しwarmup、16384呼出し×9 batch。',
           'JS→Wasm呼出しとchecksumを含む。batch約0.6–1msの診断値で、小差の性能優位を確定しない。','',
           '| 入力族 | n | 形 | ns/call中央値 | process中央値の範囲 | bytes |',
           '|---|---:|---|---:|---|---:|']
    for kind,directory in directories.items():
        m=read(directory/'manifest.json');c=read(directory/'checks.json')
        summary['correctness'][kind]={'modules':len(c['rows']),'calls':c['calls'],'traps':c['traps']}
        summary['solver_status'][kind]=dict(collections.Counter(s['status'] for row in m['rows'] for s in row['retypd']))
        for n in (1,4,8):
            for mode in ('loop','peeled'):
                vals=[x['ns_per_call_median'] for x in runtime if x['kind']==kind and x['n']==n and x['mode']==mode]
                assert len(vals)==3
                row=next(x for x in m['rows'] if x['n']==n and x['mode']==mode and 'O3' in x['file'])
                v={'kind':kind,'n':n,'mode':mode,'median_ns':statistics.median(vals),'range_ns':[min(vals),max(vals)],'bytes':row['bytes']}
                summary['runtime'].append(v)
                lines.append(f'| {kind} | {n} | {mode} | {v["median_ns"]:.3f} | {min(vals):.3f}–{max(vals):.3f} | {row["bytes"]} |')
    lines+=['','全例linear memory 65536bytes。最大RSSはNode全processの値で、アルゴリズム単体ではない。',
            'Retypdのfull solverは1条件1processの診断値。shape回復は1process内11反復の中央値で、測定法が異なる。',
            '未実行・timeout・frontend未対応を回復失敗として加算しない。NotDec本体は今回未実行。']
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (a.out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    snap=a.out/'sources';snap.mkdir()
    for f in HERE.iterdir():
        if f.is_file() and f.suffix in ('.py','.cjs','.md'):
            shutil.copy2(f,snap/f.name)
    targets=[*directories.values(),measure,BASE/'type-language-pilot-v1',a.out]
    files=set(f for d in targets for f in d.rglob('*') if f.is_file() and f.suffix!='.pyc')
    # Third party originals stay in .tools with their license; their commit is in environment.json.
    for name in ('solver.py','graph_solver.py','fast_enfa.py','schema.py'):
        files.add(ROOT/'.tools/retypd-source/src'/name)
    pins=[{'path':f.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(files)]
    (a.out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
    for item in pins:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(json.dumps({'pins':len(pins),'modules':sum(v['modules'] for v in summary['correctness'].values()),
                      'calls':sum(v['calls'] for v in summary['correctness'].values()),'shapes':len(shapes)}))


if __name__=='__main__':main()
