# -*- coding: utf-8 -*-
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
marker='## 可変二表の接続更新と履歴なし回復（2026-10-23）'
updates={
 'research/literature-review.md':'[mutable-factorの照合](mutable-factor/prior-art.md)を追加。US9117094B2 Data location obfuscationの書誌・説明概要・請求項1–19を読み、実行中の配置交換とpointer scramblingの先行性を確認した。DrapeのGeneralising the Array Split Obfuscationは査読誌書誌・出版社要旨まで。本文未読と実験結果を区別し、動的indirectionだけを新発明としない。',
 'research/research-gap.md':'[可変な二表による接続表現](mutable-factor/README.md)では、毎回異なる中間対応でも、N=B∘Aを抽象状態に選べば更新が閉じた。実行履歴の数や長さだけでは解析費用増を主張できない。公開された読出し式の合成について、小さな状態上の更新要約が存在するかを初期ゲートへ追加する。',
 'research/candidates.md':'[可変二表の案](mutable-factor/README.md)を限定Wasmへ実装し、主60本と診断36本を検査した。定数回の局所書込みで意味を保持できるが、全24factor条件は方式既知の合成関係により元rawとbyte一致するWasmへ戻る。既存data refinement/配置交換との近さと保護優位の欠如が最大のReject理由。独立した新しい三候補の一つや主特許候補として数えない。',
 'research/threat-model.md':'mutable-factorでは非公開・固定memory32内の接続とpayloadが持続し、公開run/resetの返値・trap・後続動作を保つ。回復器は配布binaryだけを読み、source・seed・manifestを受け取らない。診断memory exportは検証用で、解析に使わない。全profile照合に基づく既知方式の回復であり、任意Wasmから不変関係を自動発見する汎用解析とは区別する。',
 'research/algorithm.md':'[可変二表の更新](mutable-factor/algorithm.md)。N[i]=B[A[i]]、Aは全単射。a=A[u], b=A[w], t=B[b]を読み、A[u]=b; A[w]=a; B[a]=t; B[b]=vとする。u=wでもN[u]=vだけを実現し、旧N[u]は保存不要。一方、同じ関係が解析側の履歴不要な更新要約になる。主発明としては不採用。',
 'research/novelty-analysis.md':'[mutable-factor](mutable-factor/prior-art.md)の具体的な四store規則は実装・論証したが、動的配置交換・data refinementの先行性と、全24条件のbyte一致回復から独立した有力な新規性・保護優位は未確立。限定的な構成の成立と特許性を分け、一般的な配置変更を初めて実現したと主張しない。',
 'research/experiments.md':'[mutable-factor実測](../results/invention-20261023/mutable-factor-report-v1/report.md)。主60本126,300呼出し、診断36本75,780呼出し、計202,080で不一致0。全小モデル1,586,115比較、Z3一更新UNSAT、別WABT240呼出し。負例6個は全て検出。回復24/24は元rawとbyte一致。108process/756batchの実行費用は元の約1.40–1.99倍で、追加保護は未確認。',
 'research/novelty-status-20261023.md':'[可変二表の接続表現](mutable-factor/README.md)を実装・反証した。202,080呼出しの値・trap・診断状態は一致したが、変更履歴を展開せず全24条件を元Wasmへ戻せた。配置変更の先行性もあり主案には不採用。有力な新規特許候補の確立は未達。',
 'paper-draft.md':'**Proposed Method / Implementation.** 論理接続Nを二表の合成B∘Aで表し、書換えごとにAの二位置交換とBの補償を四storeへ融合する限定Wasm変換を作成した。\n\n**Evaluation.** 主60本126,300呼出し、診断36本75,780呼出し、期待trap計1,152件で不一致0。一更新の配列モデルは単射条件の下でZ3 UNSAT。全24変換条件は元rawとbyte一致するコードへ回復した。実行は元の約1.40–1.99倍。\n\n**Discussion / Conclusion.** 参照の合成が小さな抽象状態に閉じるため、動的な対応変更は解析側に履歴の追跡を要求しなかった。配置交換とdata refinementの先行性もあり、主特許候補には不採用。[実装と再現](research/mutable-factor/README.md)、[実測](results/invention-20261023/mutable-factor-report-v1/report.md)。'
}
for rel,body in updates.items():
    path=ROOT/rel;text=path.read_text(encoding='utf-8')
    if marker not in text:path.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+body+'\n',encoding='utf-8')
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
line='2026-10-23追補：[更新のたびに中間対応を変える二表表現](research/mutable-factor/README.md)を実装・反証。主60本と診断36本の計202,080呼出しは一致したが、全24変換条件を変更履歴なしに元とbyte一致するWasmへ回復。元の約1.40–1.99倍の実行費用に対する追加保護と独立した新規性は未確立で、主特許候補には不採用。[実測](results/invention-20261023/mutable-factor-report-v1/report.md)。'
if line not in text:path.write_text(text.replace('# webassembly_obfuscation\n','# webassembly_obfuscation\n\n'+line+'\n',1),encoding='utf-8')
path=ROOT/'research/novelty-status-20261023.md';text=path.read_text(encoding='utf-8').replace('20%使用（約80%残）','21%使用（約79%残）');path.write_text(text,encoding='utf-8')
print('Integrated mutable-factor evidence; no TeX files modified.')
