# 型回復の経路列挙を狙う仮説：既知のループ展開による対照

2026-10-21。**新しい主発明は未確立。型回復の実験基盤と、誤判定を防ぐ対照を作成した。**
局所decoderとは別原理として、型のアクセス言語による負荷増加を検討した。
実際に公開Retypdを動かし、Wasmから抽出した制約で負荷増加を観測した。
ただし、既知の末尾loop peelingで再現でき、目的としたfield形状は安く回復できた。
この結果を「解析不能」「NotDecを破った」「新規特許の完成」とはしない。

## 実装と対象

`wasm_probe.py` は二つの同値Wasmを生成する実験用生成器であり、任意Wasmへ
適用する完成した難読化CLIではない。公開memory32、3個のi32引数head/bits/itersを持つ
二分graph walk。移動回数は `n+(iters&31)`、最後にoffset 8のi32を読む。
各移動でbitsの該当bitに応じ、offset 0または4のポインタを一つだけloadする。
regular族は全移動を選択し、forced族は末尾区間の最初だけoffset 4を必ず読む。
forcedとregularは異なる関数で、各族のloop/peeled間だけ同値を要求する。

loop版は全移動を一つのloopで行う。peeled版は先頭 `iters&31` 回をloop、末尾n回を
直線命令にする。同じ順序のload列であり、値・最初の範囲外trap・memory不変を保存する。
入力整数の全bitを受け付け、Wasm shiftのmod 32を維持する。memoryは非共有。
動的graph、unaligned access、範囲外pointerも有限テストへ含めた。
実装のnは1,2,4,6,8。実メモリreadを増やすダミー操作は追加していない。

`extract` は実.wasmをWABTで読んで、load/if/loop/local更新からSSA風の型制約を作る。
O3のlocal再利用を新しいSSA値として扱う。これは診断用の限定frontendであり、
NotDecのLLVM lifting/PNDiff/全手続き間解析を代行したという主張ではない。
制約をGPLv3のGrammaTech Retypd原本へ渡す。原本は変更していない。

## 結果

- regular 20本、forced 20本：WABTとNodeでvalidation。計70,440呼出し、うち
  3,600 trap期待ケースで不一致0。memory全体は各入力群後に不変を確認。
  40本は2入力族×5の展開数×2形×raw/O3であり、40個の独立アプリではない。
- WABT `wasm-decompile` は40本全て出力成功。読みやすさやC再コンパイル成功は未採点。
- 限定frontend+Retypd：regularは40 solver実行全て正常終了。forcedは36正常終了、
  1件15秒timeout、3件は同solverのtimeout後に未実行。crashは0。
  未実行3件をtimeoutとして数えない。O3 forced n=6/8のDFA solverは未測定。
- O3 regular n=8：loopは5生成制約・DFA solver約17ms、peeledは260制約・約1,346ms。
  両者の最終sketchは7 node。forced n=8 O3のpath-expression solverは132制約・約692ms。
  solver値は1回の診断測定であり、分布・人間の解析時間ではない。
- 適応対照：同じRetypdの `compute_quotient_graph` を先に使うと、全40本でoffset
  0/4の再帰pointerとoffset 8のintegerを回復。形状処理は11反復中央値で
  0.185–1.412ms、binary読取・frontendは別に18.29–23.73ms。
  これは一般の精密な型推論を置き換える処理ではなく、この保護目標への回復である。
- 末尾fieldを12へ変えた40制約対照では回復も12へ変化し、結果を定数で返していない。
  これは40個の誤ったWasm実行テストではない。
- 40 binaryを最終生成器で再生成してbyte一致。

実行費用はO3のn=1/4/8、2族×2形×3 fresh processの36回を測定した。
各process 32,768呼出しwarmup、16,384呼出し×9 batch。JS→Wasm呼出しとchecksumを含む。
batchが約0.6–1msと短く、ばらつきもあるので小さな速度差を確立したとはしない。
全例linear memory 64KiB、Node最大RSS 43,132–45,604KiB。生成・validate・O3の組は
各1回約44.8–57.3ms。任意入力を変換するcompilerの性能ではない。

[比較表](../../results/invention-20261021/type-language-report-v2/comparison.md)、
[集計](../../results/invention-20261021/type-language-report-v2/summary.json)、
[形状回復](../../results/invention-20261021/type-language-measure-v1/shape-recovery.json)、
[regular記録](../../results/invention-20261021/type-language-wasm-v2/manifest.json)、
[forced記録](../../results/invention-20261021/type-language-forced-v1/manifest.json)。

## 解釈と先行技術

元の「NFAが大きく決定化されれば型を隠せる」という説明には二つの不足があった。
第一に、型のshapeは同一fieldを統合できる。第二に、遅い制約列挙を通らなくても
対象のfield配置を回復できる。正確なアクセス言語の列挙が遅い事実は保存するが、
目的とした構造回復の困難さとは一致しなかった。

末尾loop peelingは既知である。LLVM公式 `LoopPeel.h` の `PeelLast` は、指定数の
末尾反復を取り出すAPIを説明している。今回読んだのは宣言・説明部分で、LLVMの
pass自体を今回実行したわけではない。
https://llvm.org/doxygen/LoopPeel_8h_source.html

Retypdの `solver.py` のshape統合と、`graph_solver.py` のDFAからの経路列挙を
読んで対照を設計した。新しいsubset constructionや型推論法を発明したとはしない。
Noonan, Loginov, CokのPLDI 2016論文は今回要旨/書誌だけを確認し、本文の未読部分を
実装から推測しない。参照・source commitは[事前計画](plan.md)にある。

新規性の追加検討には、既知のloop peelingと異なる生成規則、ならびにshape回復
にも影響する測定結果が必要。nやtimeoutを増やして新発明と数えない。
最終形状が回復しても精密な型制約全てが同じ費用で得られるとは一般化しない。
有限環残差方式の限定採用は維持し、研究全体のgoalはactiveのまま。

## 再現

Python 3.9、Node 24.15.0、WABT1.0.42、Binaryen133。rootから実行し、各出力先を
未作成にする。ネットワーク取得と依存installは初回だけ。RetypdのGPLv3を保持する。

```powershell
git clone https://github.com/GrammaTech/retypd.git .tools/retypd-source
git -C .tools/retypd-source checkout 8f7f72be9a567731bb82636cc91d70a3551050bf
python -m venv .tools/retypd-python
.tools/retypd-python/Scripts/python.exe -m pip install -r results/invention-20261021/type-language-pilot-v1/requirements-freeze.txt
.tools/retypd-python/Scripts/python.exe research/type-language-gate/pilot.py results/type-new/pilot
python research/type-language-gate/wasm_probe.py results/type-new/regular
python research/type-language-gate/wasm_probe.py results/type-new/forced --forced
node research/type-language-gate/check.cjs results/type-new/regular
node research/type-language-gate/check.cjs results/type-new/forced
.tools/retypd-python/Scripts/python.exe research/type-language-gate/measure.py results/type-new/regular results/type-new/forced results/type-new/measure
```

`report.py` は今回の保存結果を固定パスで集計する。後続実験の測定先を自動選択しない。
source snapshotとfile hashはreportの `sources/`, `pins.json` に保存。
report-v1は相対/絶対path混在によりhash一覧生成時に停止した履歴。修正したv2を主結果にする。
先行する `type-language-wasm-v1` はO3 frontend未対応10件を保持した診断履歴で、
現行の40本に加算しない。`type-language-pilot-v1` は抽象制約のみで14正常終了と
4件30秒timeout。実Wasmの結果と別集計し、その初版script hashは当時のものを保持する。
