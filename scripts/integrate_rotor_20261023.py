# -*- coding: utf-8 -*-
from pathlib import Path
root=Path(__file__).resolve().parents[1]
marker='## 2026-10-23追補：状態付き切替グラフの全体合成'
items={
'research/candidates.md':'[切替グラフへの関数全体合成](rotor-synthesis/README.md)を、残差補正とは別の原理で実装した。元gateの個別置換ではなく、初期switch値と有限終点条件から接続を同時合成する。新規性は既知rotor-routing/有限合成との距離が未確立、実装可能性は3小例で確認、性能は最良でも元の5.4〜9.4倍。最大のReject理由は一般の有限仕様合成との技術差と保護効果が乏しいこと。主候補には不採用。',
'research/algorithm.md':'[生成規則と疑似コード](rotor-synthesis/README.md)を追加。bit laneごとのtoken保存、switchのmove-then-toggle、吸収sink、全初期入力に対する有限上限を用いる。descriptor評価器から直接local命令へ下ろし、最大到達回数でloopを短縮する。Wasm固有の未定義動作やtrapは使わない。',
'research/threat-model.md':'切替版はgraphと全命令が公開され、解析者は方式を知る。保護課題は循環・状態更新から簡潔な等価bitwise式を回復すること。元source/合成ログを解析器に与えない。native/tight版ではgraph descriptorも配布しない。実行可能であることを秘密保持と同一視せず、BDDによる実命令の記号追跡を適応攻撃として行った。',
'research/novelty-analysis.md':'切替グラフの訪問依存更新は既知rotor-routing、全体入出力からの接続探索は既知有限仕様合成に近い。[一次資料と読了範囲](rotor-synthesis/prior-art.md)。元gateを配布しないことだけで差別化を認定できない。3inputの微小例だけでなく、一般の生成定理・費用に見合う解除負担が必要だが未確立。',
'research/experiments.md':'[実験前計画](rotor-synthesis/plan.md)と[実測](../results/invention-20261023/rotor-synthesis-report-v1/report.md)。共通評価器と直接命令化の各24binaryを115,992呼出しずつ比較し、不一致0。別BDD回復6binaryは28,998呼出し一致。入力再利用を独立標本として合算しない。byte再現18本、WABT72呼出し。主性能45fresh process×7batch、tightのO3を0.464〜0.714msで回復。xor3の有限合成UNSATを一般的不可能性と扱わない。',
'research/research-gap.md':'元gateの構成を直接残さずgraph全体を合成しても、短い上限で終点に達することが、解析者の記号追跡にも使える。[直接命令化試験](rotor-synthesis/README.md)は共通評価器の過大な実行費用を除いても同じ限界を示した。一般ARRIVALの難しさや大きい循環から、今回の限定族の保護強度は導けない。',
'research/literature-review.md':'[追加照合](rotor-synthesis/prior-art.md)：Propp2010の著者版導入・§2.1、GärtnerほかICALP2018の書誌/要旨/定義、HaslebacherICALP2025の導入・定義、HolroydほかCPC2019の著者版pp1–5、GulwaniほかPLDI2011とJhaほかICSE2010の要旨・導入抜粋を確認。全論文を通読・再現したとは表現しない。',
'paper-draft.md':'**Abstract / Proposed Method.** 状態付き切替graphの接続を、関数全体のBoolean入出力から合成し、32laneのWasm実行へ変換した。\n\n**Evaluation.** 共通評価器、直接命令化、到達回数削減を比較。各主24binary・115,992呼出しで不一致0。必要回数を5/8/5に減らした版は元の約5.4〜9.4倍で、公開命令だけから全6 raw/O3条件を回復できた。O3解析本体0.464〜0.714ms、WABT読取り等を除く単回値。\n\n**Discussion / Limitations / Conclusion.** 既知rotor-routingと有限仕様合成以上の新規性は未確立。3inputの小例であり、解析時間の下界や汎用的な保護効果ではない。小さなBDDへ簡約できるため主特許候補には不採用。研究全体を完了とはしない。[実装・再現](research/rotor-synthesis/README.md)、[実測](results/invention-20261023/rotor-synthesis-report-v1/report.md)。'
}
for rel,body in items.items():
    path=root/rel;text=path.read_text(encoding='utf8')
    if marker not in text:path.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+body+'\n',encoding='utf8')
print('Updated',len(items),'research documents')
