# -*- coding: utf-8 -*-
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
entries={
'research/candidates.md':('2026-10-23追補：有限回更新と隠れた依存順序','[設計・実装・比較](hidden-filtration/README.md)。元DAGを任意初期stateからD回で正答へ到達する同時更新へ変換し、出力座標保存の非線形共役だけを配布した。線形観測のrank条件を検査したが、二次観測で全18条件回復。主案に不採用。'),
'research/novelty-analysis.md':('2026-10-23再開後の照合','[有限回更新系の先行技術比較](hidden-filtration/prior-art.md)。WO2012040383A1の非線形座標変換・合成簡約が近い。初期化と出力codecを不要にする限定生成規則は実装したが、独立した新規性を主張しない。低次数の共同観測から全18条件を回復した。'),
'research/experiments.md':('2026-10-23：有限回更新系の追加実験','[再現手順](hidden-filtration/README.md)、[実測表](../results/invention-20261023/hidden-filtration-report-v1/report.md)。主307,656呼出し、追加回復153,828呼出し、scratch4,608、WABT96が一致。SMTは回復18pureモデルについてUNSAT。36process・252batchの時間/size/memory/変換時間を保存。初期解析器のtimeoutを保護成功に数えない。'),
'research/research-gap.md':('2026-10-23：低次数の共同観測が残る問題','[有限回更新系](hidden-filtration/algorithm.md)では、入力・出力に独立したcodecを残さず、一段の線形観測も消せた。しかし低次数の逆座標が共同観測の辞書に含まれ、等価な計算を抽出できた。次は可逆座標変換に依存しない具体的生成を検討する。その場合も既知の商表現・simulation・データ表現合成との差を確認する。'),
'research/literature-review.md':('2026-10-23：座標変換・有限回収束・観測の持上げ','[読了範囲と書誌一覧](hidden-filtration/prior-art.md)を追加。近接公報はHriljacのWO2012040383A1。有限回収束はRichard（Discrete Applied Mathematics,2019）、観測の持上げはMauroy/Goncalves（CDC2016, DOI10.1109/CDC.2016.7799269）を照合。公報の説明読了と論文の要旨のみの確認を区別し、既存評価を再現したとはしない。'),
'paper-draft.md':('2026-10-23追補：有限回更新系による別候補の評価','**Abstract / Proposed Method.** pure i32式DAGを同時更新へ変え、出力座標を保存する非線形共役を施す。任意初期状態から固定回数で正しい出力へ至るため、初期・出力codecを配布しない。既知座標変換との独立性は未確立。\n\n**Evaluation.** 主307,656呼出しが一致。一次観測では非線形版の解析が停止したが、二次観測への持上げでraw/O3全18条件が回復した。非線形版は0.12–4.75秒、回復18モデルは64bit入力全体のSMT照合でUNSAT。線形版に対し解析費用は約10–57倍、実行費用は約3.2–5.6倍。\n\n**Discussion / Limitations / Conclusion.** 小規模3関数・1seed・独自評価器に限定され、元版比の実行費用も大きい。WO2012040383A1に近接し主発明には採用しない。初期解析器のtimeoutは消去の効率改善で解消し、保護効果から除外した。[生成規則](research/hidden-filtration/algorithm.md)、[実測表](results/invention-20261023/hidden-filtration-report-v1/report.md)。')}
for file,(title,body) in entries.items():
    path=ROOT/file;old=path.read_text(encoding='utf8')
    if title not in old:path.write_text(old+'\n## '+title+'\n\n'+body+'\n',encoding='utf8')
print('Integrated',len(entries),'documents')
