# -*- coding: utf-8 -*-
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
marker='transition-square/README.md'
paragraph='''[遷移二乗と双模倣評価](research/transition-square/README.md)を実Wasmへ実装した。主54条件106,488呼出し、境界48条件24,960呼出しは一致したが、公開行列の平方根とBoolean抽出で主24条件・境界12条件をすべて回復。同じgraph評価器に対して約26–37%高速化した一方、元の式比約811–8,643倍の実行費用。回路還元・行列関数の先行性と公開逆算から主特許候補には不採用。[実測](results/invention-20261023/transition-square-report-v1/report.md)。'''
readme=ROOT/'README.md';old=readme.read_text(encoding='utf-8')
if marker not in old:
    head,rest=old.split('\n',1);readme.write_text(head+'\n\n2026-10-23追補：'+paragraph+'\n'+rest,encoding='utf-8')
notes={
 'experiments.md':'682小graph・32,916partitionの全数検査、source式と抽出BDD24件のSMT UNSAT、別WABT162呼出し、3拒否対照、36process/252batch、反復counter8,736呼出しを保存。v1のflag不足、v2のO3未対応は保護効果に数えず、v3を主値とした。',
 'literature-review.md':'最も近い核はChen / van Breugel / Worrell, FoSSaCS 2012, DOI10.1007/978-3-642-28729-9_29の確率的双模倣への回路還元。著者版§2と書誌を閲覧した。主平方根・三角漸化式にはHighamの一次解説を確認し、[閲覧範囲と特許検索](transition-square/prior-art.md)に記録した。',
 'candidates.md':'値の符号化から関係判定問題へ移る候補だが、回路還元自体は既知である。追加の遷移合成も公開可逆な行列関数に還元された。2seed、最適化設定、実装上の修正を独立した発明として数えない。',
 'research-gap.md':'保存する観測を全partitionのlumpabilityに強めると、公開多項式逆算が意味保存と解除の両方を与えた。計算問題を置き換えるだけでは費用に見合う保護にならない。単なる指数・seed変更へ進まない。',
 'novelty-analysis.md':'独立した新規性は未確立。評価器の高速化は反復数減少で説明できるが、既存最良の双模倣実装との比較ではない。最悪計算量のP-completenessを小さい生成例の保護強度へ転用しない。',
 'threat-model.md':'方式既知、binary公開。source・seed・正解graphは解除器へ渡さず、等価なBoolean式の回復を目標とした。pureな単一i32式profileに限定され、元のmemory副作用・trap・再入を含む汎用変換ではない。',
 'algorithm.md':'[具体構成と疑似コード](transition-square/algorithm.md)。L=(I+P)/2、Q=L^2を配布し、整数のpartition refinementで実行する。P^2のみでは誤答。主平方根からの逆算と、限定した意味保存の論証を両方保存した。',
 'novelty-status-20261023.md':'新しい主特許候補の確立は未達。方式の動作、比較上の高速化、難読化の保護効果を区別し、この案は主案へ昇格しない。研究全体は継続する。'}
for name,extra in notes.items():
    path=ROOT/'research'/name;text=path.read_text(encoding='utf-8')
    if marker in text:continue
    note=paragraph.replace('(research/','(').replace('(results/','(../results/')
    path.write_text(text+'\n\n## 遷移二乗による双模倣評価（2026-10-23）\n\n'+note+'\n\n'+extra+'\n',encoding='utf-8')
paper=ROOT/'paper-draft.md';text=paper.read_text(encoding='utf-8')
if marker not in text:
    paper.write_text(text+'\n\n## 追加評価：遷移二乗と公開平方根による解除（2026-10-23）\n\n'+paragraph+'''\n\n回路から双模倣判定への既知還元に対し、自己遷移と2段遷移の合成でgate境界を弱める仮説を検査した。生成graphのスペクトル条件により、合成行列から主平方根を一意に回復できる。この条件は全partitionの意味保存を説明すると同時に、公開binaryからの解除方法を与える。小モデル682 graphと32,916partitionで照合し、主24条件の回復式はSMTで元のBoolean式と同値だった。\n\n同じ評価器を使うbase対照よりsquareは約26–37%速く、診断Wasmの8,736呼出しで分割反復数の減少を確認した。ただし通常の式より大幅に遅く、既知の最良bisimulationアルゴリズムとの比較でもない。この否定結果は計算問題変更一般の不可能性を示さず、本生成族の保護と費用の限界を示す。汎用decompilerの未対応やツール設定の失敗を成功率へ算入していない。\n''',encoding='utf-8')
print('Integrated transition-square evidence; no changes to paper/main.tex or paper/README.md')
