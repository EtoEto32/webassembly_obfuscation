"""Export saved static timings without running Wasm or repeating measurements."""
import csv
import json
from benchmark_normalization_processing import OUT, ROOT, sha


def main():
    report = json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    selection = json.loads((OUT/'selection.json').read_text(encoding='utf-8'))
    assert sha(OUT/'selection.json') == report['selection_sha256']
    assert sha(ROOT/'scripts/benchmark_normalization_processing.py') == report['evaluator_sha256']
    assert not report['target_wasm_executed'] and not report['hash_throughput_measured']
    rows = report['summaries']
    assert len(rows) == 24 and len(report['records']) == 168
    for row in rows:
        records = [r for r in report['records'] if not r['warmup'] and r['source'] == row['source'] and r['method'] == row['method']]
        assert len(records) == 6 and all(r['valid'] for r in records)
        assert {r['output_sha256'] for r in records} == {row['stable_output_sha256']}
    with (OUT/'summary.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ['# 正規化前処理時間の反復比較', '', '2026-10-10。この前処理時間の比較では採掘Wasmを起動していない。', '',
        '## 方法', '',
        '6入力・4処理を1回ウォームアップ後に各6回測定し、入力と処理順序を回転した。168記録中144記録が測定対象。', '',
        '入力読出し・作業コピー保存、逆アセンブル／規則適用／組立または最適化、出力保存、WABT最終検証を計時した。SHA計算・ログ保存は範囲外。Pythonは再利用し、外部ツール起動は含む。アルゴリズム単体ではなく実装した処理全体の時間である。', '',
        '## 結果', '', '単位ms、中央値（最小値–最大値）。範囲は信頼区間ではない。', '',
        '| 入力 | WAT往復 | 専用規則併用 | Binaryen局所 | Binaryen O2 |', '|---|---:|---:|---:|---:|']
    labels = ['SWAMPED基準版', 'SWAMPED NOP挿入', 'SWAMPED定数分割', 'xmr命令置換', 'A-Star計測', 'CreaturePack通常']
    for label, item in zip(labels, selection['inputs']):
        values = []
        for method in selection['methods']:
            r = next(r for r in rows if r['source'] == item['source'] and r['method'] == method)
            values.append(f"{r['median_ms']:.1f}（{r['min_ms']:.1f}–{r['max_ms']:.1f}）")
        lines.append('| '+label+' | '+' | '.join(values)+' |')
    lines.extend(['', '24条件すべてで6反復の出力SHAが一致し、全記録でWasm検証が成功した。専用・Binaryenの18条件は既存比較の出力SHAとも一致した。', '',
        '## 判断と限界', '',
        '専用処理の中央値120.1–781.1msに対し、局所最適化は36.6–171.7msで、今回の6入力では専用処理が長かった。単純定数分割は既存最適化でも整理でき、専用処理の速度上の利点は確認できない。一部の生成標本の基準バイト一致と、最適化による他命令の変更は別に評価する。バイト一致だけで意味保存や検知の優位性を示さない。', '',
        '単一ホスト・6反復・温まったファイルキャッシュ・CPU affinityなし。逆アセンブル／テキスト処理／組立や起動境界が異なり、アルゴリズムの優劣に一般化しない。旧記録の規則適用のみの時間とは混在させない。式解析時間は今回の比較外。正規化後のハッシュ出力・速度は別の実験であり、進捗と結果はdocs/countermeasure-runtime-plan.mdおよびdocs/countermeasure-experiment-report.mdを参照する。', '',
        '## 再現と根拠', '',
        'リポジトリルートで `.tools/runtime-analysis-py312/Scripts/python.exe scripts/benchmark_normalization_processing.py`。対象Wasmを実行せず静的処理だけを再測定する。', '',
        '- `results/countermeasures/processing-timing/selection.json`：入力・ツールSHA、版、環境、範囲。',
        '- `results/countermeasures/processing-timing/results.json`：生記録、順序、出力SHA、集計。',
        '- `results/countermeasures/processing-timing/summary.csv`：24条件の集計。',
        '- `results/countermeasures/processing-timing/processing-times.png`・`.svg`：比較図。',
        '- `scripts/report_normalization_processing.py`：保存結果の確認と本報告・CSVの生成。',
        '- `scripts/plot_normalization_processing.py`：保存結果の描画。', ''])
    (ROOT/'docs/countermeasure-processing-time.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(dict(summary_conditions=24, measured_records=144, stable_outputs=True)))


if __name__ == '__main__':
    main()
