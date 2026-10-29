# -*- coding: utf-8 -*-
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
marker='有限環の4点実行の追補（2026-10-19）'
note=marker+'：[次数によらない4点合成](nilpotent-stencil/README.md)をWasmへ実装。256の倍数の入力摂動により評価点変数の4次以上が消える性質を使い、各laneが非単射でも4結果から元出力を得る。主70本・300,160呼出し、追加60本・257,280呼出し、WABT420呼出しで不一致0。誤変換3種の反例、非単射4組、正の追加対照6本・25,728呼出しを検査。方式既知の定数係数射影で30/30条件を回復し、そのscalarモデルはSMTで同値。主70本のbyte再現も一致。共通Wasm内部loopの105 fresh processでは動的版が元の約4.1–5.7倍の時間を要し、元次数を増しても解析は保持次数3に閉じる。既知の自己還元・符号化計算との差と追加保護優位性が弱く主方式には不採用。独立した新規性の確立と特許を目指す主目標は未達、goalはactive。\n\n'
for relative in ['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']:
    path=ROOT/relative;text=path.read_text(encoding='utf-8')
    if marker in text:continue
    addition=note
    if relative.startswith('research/patent/'):addition=note.replace('(nilpotent-stencil/README.md)','(../nilpotent-stencil/README.md)')
    elif relative=='paper-draft.md':addition=note.replace('(nilpotent-stencil/README.md)','(research/nilpotent-stencil/README.md)')
    head,sep,tail=text.partition('\n');path.write_text(head+'\n\n'+addition+tail if sep else text+'\n\n'+addition,encoding='utf-8')
