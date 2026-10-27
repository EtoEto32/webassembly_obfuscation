# -*- coding: utf-8 -*-
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MARK='例外参照packetの追補（2026-10-19）'
FILES=['research/STATUS.md','research/literature-review.md','research/research-gap.md','research/candidates.md','research/threat-model.md','research/algorithm.md','research/novelty-analysis.md','research/experiments.md','research/patent/README.md','paper-draft.md']
for name in FILES:
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if MARK in text:continue
    link='exception-packet/README.md' if name.startswith('research/') else 'research/exception-packet/README.md'
    if name=='research/patent/README.md':link='../exception-packet/README.md'
    note=(f'{MARK}：[条件の遅延解釈と共有]({link})を実Wasmへ実装した。3方向を比較し、二タグの例外参照をSSA条件ごとに共有する案を検査した。主72 target＋72回復、147,456呼出しで不一致0。追加mutable条件等24,864呼出し、互換性・宣言順9,216呼出し、WABT288呼出しも一致。packet方式36/36を通常selectへ回復し、主全体でもcontrol outcomeは最大2。108 fresh processでK=48の共有はfreshより約6.6–12.4倍高速だが、通常helperより約81–143倍遅く、解析の追加費用は約2.5–3.5倍。SMTのscalar比較は68/72がunsat、4はunknown。別の交換・結合則照合が当該4を含む60/72で一致し、両検査の和集合は72/72。全binaryの形式証明ではない。72本の再生成byte一致、誤handler・nullの反例、4拒否対照を保存。DAG処理の不備、確認器のlocal上限、WABTの非null block型未対応は保護効果に数えない。例外難読化と通常の共通化に対する独自性・効果が弱く主案には不採用。新規で有効な主発明と特許性の確立は未達、goalはactive。\n\n')
    if text.startswith('# '):
        first,sep,rest=text.partition('\n');text=first+'\n\n'+note+rest.lstrip('\n')
    else:text=note+text
    path.write_text(text,encoding='utf-8')
