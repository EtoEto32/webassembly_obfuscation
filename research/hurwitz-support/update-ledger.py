# -*- coding: utf-8 -*-
"""Append-only-in-spirit, idempotent research ledger entry for this experiment."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
marker = '入力依存の置換列書換えの追補（2026-10-19）'
note = ('{marker}：[支持制限付きHurwitz変換]({link})を実Wasmへ実装。'
        '既知の幅5置換計算・固定基底変更・局所表融合と比較した。'
        '主100本と追加36本、計2,943,776呼出しで不一致0、WABT600呼出しも一致。'
        '主4非定数例＋1定数対照、追加2非定数例を分けて記録した。'
        '全66回復条件（非定数56、定数10）で元式と同じ正規ROBDDを得た。'
        '局所逆書換えが止まっても、出力に必要な5値の意味状態を追えば回復できる。'
        '通常O3後も変換は残るが、固定基底変更に対する意味解析時間比は約0.97–1.29、'
        'binaryは約3倍で、明確な追加優位性は未確認。90 fresh process、'
        '100主binaryのbyte再現、28,800＋8,192代数検査、誤交換反例と4拒否対照を保存。'
        'v1の再帰処理不備による中断は解析耐性に数えない。'
        'US20240045670A1・US9654280B2の関連記載と請求項を読んだ範囲を明記した。'
        '独立した新規性と効果が弱く主発明には不採用。'
        '主目標は未達、goalはactive。外部公開・push・出願は行っていない。')
files = ['research/STATUS.md', 'research/literature-review.md',
         'research/research-gap.md', 'research/candidates.md',
         'research/threat-model.md', 'research/algorithm.md',
         'research/novelty-analysis.md', 'research/experiments.md',
         'research/patent/README.md', 'paper-draft.md']
for name in files:
    path = ROOT / name
    text = path.read_text(encoding='utf-8')
    if marker in text:
        continue
    link = ('research/hurwitz-support/README.md' if name == 'paper-draft.md'
            else '../hurwitz-support/README.md' if name.startswith('research/patent/')
            else 'hurwitz-support/README.md')
    first, rest = text.split('\n', 1)
    path.write_text(first + '\n\n' + note.format(marker=marker, link=link)
                    + '\n' + rest, encoding='utf-8')
    print(name)
