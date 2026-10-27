# -*- coding: utf-8 -*-
"""Summarize saved observations; does not run or overwrite experiments."""
import collections
import hashlib
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main(base, output):
    base, out = pathlib.Path(base), pathlib.Path(output)
    out.mkdir(parents=True, exist_ok=False)
    def read(folder, file):
        return json.loads((base / folder / file).read_text(encoding='utf8'))
    m = read('span-mask-main-v1', 'manifest.json')
    checks = read('span-mask-main-v1', 'checks.json')
    io = read('span-mask-io-v1', 'results.json')
    peel = read('span-mask-peel-v1', 'results.json')
    perf = read('span-mask-runtime-v1', 'summary.json')
    audit = read('span-mask-audit-v1', 'audit.json')
    node = read('span-mask-audit-v1', 'audit-node.json')
    verified = 0
    for name in ('main', 'io', 'peel', 'runtime', 'audit'):
        folder = base / ('span-mask-' + name + '-v1')
        pins = json.loads((folder/'sha256.json').read_text(encoding='utf8'))
        for file, digest in pins.items():
            assert hashlib.sha256((folder/file).read_bytes()).hexdigest() == digest, (folder, file)
            verified += 1
    lines = ['# 入力依存の線形包表現：保存結果の集計', '',
             '2026-10-23。自動集計。主発明への採用を見送る。新規性・実用的な保護優位は未確立。', '',
             '## 正当性', '',
             f"主検証：{len(checks['targets'])}本、{checks['calls']:,}呼出し、不一致{checks['mismatches']}。初回チェックの再実行分は加算しない。",
             f"追加Node検証：{node['calls']:,}呼出し。scratch初期値変更：{node['scratch_calls']:,}呼出し。不一致{node['mismatches']}。",
             f"WABT：{sum(x['calls'] for x in audit['interpreter']):,}呼出し。独立GF(2)モデル：{audit['model_cases']}構成、{audit['model_assignments']:,}入力。byte再生成：{len(audit['replays'])}本。",
             'これらは適用範囲内の検査であり、実装全体の全入力同値性証明ではない。', '',
             '## 方式既知の解析', '',
             '|解析|条件数|復元|node上限|timeout|', '|---|---:|---:|---:|---:|']
    for method in ('direct', 'coefficient'):
        rows = [r for r in m['recoveries'] if r['method'] == method]
        c = collections.Counter(r['status'] for r in rows)
        lines.append(f"|{method}|{len(rows)}|{c['recovered']}|{c['node_budget']}|{c['timeout']}|")
    c = collections.Counter(r['status'] for r in peel)
    lines += [f"|逆shear簡約＋BDD|{len(peel)}|{c['recovered']}|{c['node_budget']}|{c['timeout']}|",
              f"|packed入出力全数学習|{len(io)}|{sum(r['source_bdd_equal'] for r in io)}|0|0|", '',
              '主解析のnode上限は300,000。上限到達は未復元を意味し、一般的な解析不可能性を意味しない。主系列の対象内で未対応・クラッシュは0件。対象外命令と偽kernelは別の拒否試験である。', '',
              '|入力数・例|入力依存版の全数問い合わせ回数|問い合わせms|BDD構築ms|出力BDD nodes|',
              '|---|---:|---:|---:|---:|']
    for r in io:
        if r['mode'] == 'dependent':
            lines.append(f"|{r['fixture']}|{r['queries']:,}|{r['query_ms']:.3f}|{r['construction_ms']:.3f}|{r['output_nodes']}|")
    lines += ['', '問い合わせは各i32の32bitを独立入力として使う。warmup 1,024回は表の回数に含めない。上表は1回の測定で、分散は未評価。query時間は読取・compile・BDD構築・出力compileを含まない。元式は復元後の採点だけに使用する。', '',
              '## 性能', '',
              '全coreをO3で最適化してから同一の未最適化Wasm呼出しwrapperを付加。3 process×7 batches。各process中央値の中央値、単位ns/call。元式は人工Boolean式であり、一般アプリの費用を代表しない。', '',
              '|例|元版|spanのみ|固定混合|入力依存|復元版|入力依存/固定|',
              '|---|---:|---:|---:|---:|---:|---:|']
    for f in m['fixtures']:
        ts = {t['mode']:t for t in perf['targets'] if t['fixture'] == f}
        vals = [f"{ts[k]['median_ns']:.3f}" for k in ('plain','span','constant','dependent','recovered')]
        lines.append('|'+f+'|'+'|'.join(vals)+f"|{ts['dependent']['median_ns']/ts['constant']['median_ns']:.3f}|")
    lines += ['', '|例|元版bytes|span bytes|固定混合bytes|入力依存bytes|入力依存変換ms|',
              '|---|---:|---:|---:|---:|---:|']
    for f in m['fixtures']:
        ts = {t['mode']:t for t in perf['targets'] if t['fixture'] == f}
        tr = next(t for t in m['transforms'] if t['fixture'] == f and t['mode'] == 'dependent')
        lines.append('|'+f+'|'+'|'.join(str(ts[k]['core_bytes']) for k in ('plain','span','constant','dependent'))+f"|{tr['elapsed_ms']:.3f}|")
    rss = [r for t in perf['targets'] for r in t['rss_kib']]
    lines += ['', f"{perf['processes']} process、{perf['batches']} batches、10ms未満{perf['batches_under_10ms']} batches。process RSSは{min(rss):,}–{max(rss):,} KiB。専用linear memoryは変換版65,536bytes、元版・復元版0bytes。RSSはNode全体でありWasmだけの使用量ではない。",
              '変換時間は生成・WAT出力・コンパイル・validation込みの単回測定、O3は別。ウォームアップ16,384回、校正20ms目標、CPU affinity/frequencyは未固定。raw.jsonに全測定、summary.jsonにprocess中央値とbatch範囲を保存した。', '',
              '## 判断', '',
              '固定混合を消す前処理で、固定版と入力依存版の差は確認した。しかし入力依存版も全数学習で3例全て復元し、逆shear簡約でも2例を復元した。残る24入力例の逆shear＋BDD失敗は、別攻撃による復元と区別する。',
              '実行費用は固定混合の約3.8–11.4倍、元版の約482–5,945倍。等費用に調整した最良既存方式との優位比較は未実施。近い既知原理を移植しただけという新規性上の問題もあり、主特許候補には採用しない。',
              f'この集計時に保存済み{verified}件のSHA-256 pinsを確認した。外部公開・push・出願は行っていない。', '']
    (out/'report.md').write_text('\n'.join(lines), encoding='utf8')
    shutil.copyfile(__file__, out/'report.py')
    (out/'verification.json').write_text(json.dumps({'verified_pins':verified,'main_calls':checks['calls'],'node_calls':node['calls'],'scratch_calls':node['scratch_calls'],'io_queries':sum(r['queries'] for r in io)},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'report':str(out/'report.md'),'verified_pins':verified}))


if __name__ == '__main__':
    main(*sys.argv[1:])
