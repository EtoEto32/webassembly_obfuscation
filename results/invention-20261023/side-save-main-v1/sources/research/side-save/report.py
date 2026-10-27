# -*- coding: utf-8 -*-
import ast
import json
from pathlib import Path
import platform
import statistics
import sys
import prototype as p


def main(main_dir,model_dir,holdout_dir,runtime_dir,audit_dir,dest):
    dirs=[Path(x).resolve() for x in (main_dir,model_dir,holdout_dir,runtime_dir,audit_dir)]
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    def read(i,name):return json.loads((dirs[i]/name).read_text(encoding='utf-8'))
    checks=read(0,'checks.json');manifest=read(0,'manifest.json');attacks=read(0,'attacks.json');model=read(1,'model.json');extra=read(2,'holdout.json');runtime=read(3,'summary.json');audit=read(4,'audit.json')
    rows=[]
    for t in manifest['targets']:
        if t['mode']!='side' or t['opt']!='O3':continue
        z=t['meta'];rows.append(dict(name=t['name'],seed=t['seed'],basis_saved=z['joint_rank'],side_saved=z['entry_saved_bytes'],side_temporary=z['temporary_values'],side_declared_locals=z['entry_saved_bytes']+z['temporary_values'],basis_declared_locals=z['joint_rank']))
    measured=[]
    for name in manifest['fixtures']:
        group={row['mode']:row for row in runtime['rows'] if row['name']==name}
        measured.append(dict(name=name,**group,side_over_basis=group['side']['median_ns']/group['basis']['median_ns'],side_over_plain=group['side']['median_ns']/group['plain']['median_ns']))
    def interval(xs):return dict(min=min(xs),median=statistics.median(xs),max=max(xs))
    summary=dict(node_calls=checks['calls'],node_traps=checks['traps'],node_mismatches=sum(x['mismatches'] for x in checks['rows']),
                 negative_conditions=len(checks['negative']),positive_conditions=len(checks['rows']),
                 recoveries={mode:{s:sum(x['mode']==mode and x['status']==s for x in attacks) for s in ('success','unsupported','crash','timeout')} for mode in ('basis','side')},
                 saves=rows,runtime=measured,processes=runtime['processes'],batches=runtime['batches'],short_batches=runtime['under_10ms'],
                 model_instances=model['instances'],model_state_prefix_checks=model['state_prefix_checks'],model_minimum_mismatches=model['minimum_rank_mismatches'],holdout_instances=extra['instances'],holdout_minimum_mismatches=extra['mismatches'],
                 wabt_calls=audit['calls'],wabt_traps=audit['traps'],wabt_memory_probes=audit['memory_probes'],replayed=len(audit['replay']),rejected=len(audit['rejected']),
                 side_transform_ms=interval([t['meta']['transform_ms'] for t in manifest['targets'] if t['mode']=='side' and t['opt']=='raw']),
                 side_recovery_ms=interval([r['ms'] for r in attacks if r['mode']=='side']))
    p.q.save(out/'summary.json',summary)
    text='''# 副情報による退避量削減の実測

同じ符号化表現Bを維持して、全trap prefixの修復に必要な入口保存情報を減らす生成器を実装した。最小性はnestedな副情報・線形な共有保存という限定モデル。coded side-informationとの近接性があり、独立した新難読化・特許性は未確立。

|構造|basis入口値|side入口値|side temporary|basis ns|side ns|side/basis|side/plain|
|---|---:|---:|---:|---:|---:|---:|---:|
'''
    for r in measured:
        z=next(x for x in rows if x['name']==r['name'] and x['seed']==211070)
        text+='|%s|%d|%d|%d|%.3f|%.3f|%.3f|%.3f|\n'%(r['name'],z['basis_saved'],z['side_saved'],z['side_temporary'],r['basis']['median_ns'],r['side']['median_ns'],r['side_over_basis'],r['side_over_plain'])
    text+='''
入口保持量は2seedとも一致、性能はseed211070のみ。rotate32は約13.8%時間短縮。swap16はprocess分散が重なるため明確な高速化とは言えず、ladder64は約0.4%増。宣言local総数とcode sizeは増加。入口の独立byte値をi32 localへ格納しているため、総メモリ削減やstack最小化とは主張しない。

正42条件37,184呼出し、期待trap19,152で不一致0。全64KiB physical memoryとdigestを各回検査。bad12条件は全て反例。既存回復器を変更せずbasis12、side12を元sourceとbyte一致するWasmへ回復した。別WABT294呼出し・168trap・最終memory1,652点が一致。54本byte再現、3未対応拒否を検査した。

小モデル6,048問題を全16subspaceの最小値と比較し一致、145,152状態prefix比較も一致。追加の4次元1,000問題を全67subspaceと比較し一致。全入力についての実装の機械証明ではない。

27 fresh process・189 batch、warmup32,768、15msへcalibration、全batch10ms以上。別Wasm moduleからvarying safe failを渡す。正常終了のみ、状態を繰り返し更新する固定copy列、3process中央値の中央値。Node全体RSSは測定したが、CPU register/stack使用は未測定。linear memoryは全条件1page。CPU affinityなし。transform/recoveryは各条件1回の診断値。

[再現手順](../../../research/side-save/README.md)と[算法・交換論証](../../../research/side-save/algorithm.md)。各入力folderとreportにsource snapshotとSHA-256を凍結した。snapshotは実験後で、実験開始時刻の暗号学的証明ではない。改良は工学的な部品として保持し、追加の解析耐性を示したとは扱わない。
'''
    (out/'report.md').write_text(text,encoding='utf-8')
    raw=read(3,'raw.json')[0]['measurement']
    p.q.save(out/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),node=raw['node'],v8=raw['v8'],cpu=raw['cpu'],flags=raw['flags'],wabt=p.q.w.tool('wasm-validate',['--version']).strip(),binaryen=p.q.w.tool('wasm-opt',['--version']).strip()))
    files=[f for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.md','.cjs')]
    files += [p.ROOT/f for f in ('research/prefix-repair/prototype.py','research/prefix-repair/recover.py','research/prefix-repair/check.cjs','research/copy-centralizer/model.py','research/isotope-swizzle/prototype.py','research/connectivity-elimination/prototype.py','research/loss-flag/bench.cjs')]
    pins=[]
    for folder in dirs+[out]:
        if (folder/'provenance.json').exists():raise FileExistsError('already frozen')
        for f in files:
            if f.suffix=='.py':ast.parse(f.read_text(encoding='utf-8'))
            dst=folder/'sources'/f.relative_to(p.ROOT);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(f.read_bytes())
        entries=[dict(file=str(f.relative_to(folder)),sha256=p.q.digest(f)) for f in sorted(folder.rglob('*')) if f.is_file()]
        p.q.save(folder/'provenance.json',entries);pins.extend((folder,e) for e in entries)
    for folder,e in pins:
        if p.q.digest(folder/e['file'])!=e['sha256']:raise AssertionError('hash mismatch')
    print(json.dumps(dict(verified_hashes=len(pins),node_calls=summary['node_calls'],saves=rows,ratios=[dict(name=r['name'],ratio=r['side_over_basis']) for r in measured])))


if __name__=='__main__':main(*sys.argv[1:])
