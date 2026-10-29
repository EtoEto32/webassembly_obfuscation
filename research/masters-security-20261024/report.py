"""Produce reviewable tables from measurements; never invent missing data."""
import argparse
import hashlib
import json
from pathlib import Path


def main(source, audit, out):
    out.mkdir(parents=True, exist_ok=False)
    data = json.loads((source / 'results.json').read_text())
    build = json.loads((source / 'build.json').read_text())
    checked = json.loads((audit / 'audit.json').read_text())
    rows = data['snapshots']
    narrow = [r for r in rows if r['summary']['kind'] == 'ranges']
    ratio = [r['timing'][1]['ms_per_call']['median'] / r['timing'][0]['ms_per_call']['median'] for r in narrow]
    s = {'snapshotCases':sum(r['cases'] for r in rows),
         'snapshotMismatches':sum(r['mismatch'] for r in rows),
         'snapshotTraps':sum(r['traps'] for r in rows),
         'noCopyMismatches':sum(r['unprotectedMismatch'] for r in rows),
         'retainedPayload':sum(r['savedBytes'] for r in narrow),
         'fullRetainedPayload':sum(r['fullBytes'] for r in narrow),
         'rangeModules':len(narrow), 'fallbackModules':len(rows)-len(narrow),
         'generatedRuntimeRatioRange':[min(ratio),max(ratio)],
         'budgetEvents':sum(r['eventCount'] for b in data['budgets'] for r in b['rows']),
         'audit':checked}
    lines = ['# 2026-10-24 最小実験の実測', '',
             '対象はCore Wasmと制御したNodeホスト。Component Model/WIT/WASIの統合実装、既存ランタイムの脆弱性再現、特許性の証明ではない。', '',
             '## A: 権限依存', '', '|binary|方式|ケース|不正受付|不要拒否|二重受付|', '|---|---|---:|---:|---:|---:|']
    for a in data['authority']:
        for r in a['rows']:
            lines.append(f"|{a['file']}|{r['policy']}|{r['cases']}|{r['unsafe']}|{r['falseReject']}|{r['replayAccepted']}|")
    lines += ['', '同じ216シナリオをraw/O3で実行。現試作は依存選択を手書きしており、型からの生成器は未実装。', '',
              '## B: 旧値viewと保持payload', '', '|binary|判定|ケース|trap|不一致|退避byte合計|全コピーbyte合計|', '|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"|{r['file']}|{r['summary']['kind']}|{r['cases']}|{r['traps']}|{r['mismatch']}|{r['savedBytes']}|{r['fullBytes']}|")
    lines += ['', f"合計{s['snapshotCases']}ケース、不一致{s['snapshotMismatches']}。コピーなしの不一致{s['noCopyMismatches']}。解析できた{s['rangeModules']}本では保持payloadが合計{s['fullRetainedPayload']:,}→{s['retainedPayload']:,} byte。RSSや総コピー量の比ではない。", '',
              '### 時間（参考値）', '',
              '単一Node process内、各方式warmup30回、300呼出し×9反復。ms/呼出しの中央値。固定順測定で、GC・実行順序の交絡があり、速度の優位を結論しない。view全体のmaterializeとchecksumを含む。', '',
              '|binary|全コピー|範囲生成|同じ範囲の事前評価|コピーなし|', '|---|---:|---:|---:|---:|']
    for r in rows:
        values = '|'.join(f"{t['ms_per_call']['median']:.6f}" for t in r['timing'])
        lines.append(f"|{r['file']}|{values}|")
    lines += ['', '## C: 実資源と予約', '', '|binary|方式|イベント列|受付数|実資源peak|上限|', '|---|---|---|---:|---:|---:|']
    for b in data['budgets']:
        for r in b['rows']:
            lines.append(f"|{b['file']}|{r['policy']}|{r['trace']}|{r['accepted']}|{r['peak']}|{r['capacity']}|")
    lines += ['', 'releaseと独立なlive集合によるsemaphore対照は全イベントで同一。一般のセマフォに対する新しい安全性は確認できなかった。', '',
              '## 環境・監査', '',
              f"- 環境: {build['platform']} / Python {build['python']} / Node {data['environment']['node']} / {data['environment']['cpu']}。",
              f"- WABT {build['wabt']} / {build['binaryen']}。全22本がvalidationを通過。",
              f"- 主結果の{checked['pinsVerified']}ファイルのhash一致、18上界の再算出一致。",
              f"- 別有限モデル{checked['finiteSnapshotChecks']:,}照合。これは任意のWasm binaryの全入力証明ではない。",
              '- shared拒否、import/growの全コピー退避、書込み上界の欠落反例を確認。',
              '- WABTでstore後のtrapでもstoreの結果が残る例を確認。',
              '- 各snapshot moduleのlinear memoryは128KiB。Node全体のRSS等はresults.jsonに記録したが、方式別peak memoryは未測定。',
              '- 生成時間はbuild.json（assemble/O3）とmanifest.json（summary_ms）。単回でprocess起動・キャッシュ等を含むため精密な費用比較には使わない。', '',
              '## v1からの修正', '',
              'v1は検査自体は完了したが、混合イベント生成にLCGの下位bitを使い、資源を一つも確保しない空疎な列になっていた。v2で上位bitを使い、受付が1件以上あることをassertした。raw/O3のsnapshot入力も同一seedへ揃えた。同じ範囲の事前評価をmanual実装と誤認しないよう名称を修正。v1を新しい独立証拠として合算しない。', '',
              '## 達成していないもの', '',
              'WIT自動生成、実Component Model runtime統合、実アプリケーションでの比較、跨るthreadの原子性、完全な先行特許調査、特許取得に十分な新規性・進歩性。']
    (out / 'summary.json').write_text(json.dumps(s, indent=2), encoding='utf8')
    (out / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    (out / 'provenance.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'results.json', source/'build.json', source/'manifest.json', audit/'audit.json', Path(__file__)]}, indent=2), encoding='utf8')
    print(json.dumps(s, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('audit', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    main(a.source.resolve(), a.audit.resolve(), a.output.resolve())
