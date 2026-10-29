# 同じ型付きスタック状態を結ぶ分割点による平坦化

2026-10-18、実装前の計画。接続グラフ・丸め補正から離れ、Wasmのblock/loop parameterとbranch payloadを使う。新規性と効果は未確認。標準機能の使用自体を発明とは呼ばない。

## 規則

元の命令列を型スタックで走査し、各境界の型列Sを計算する。空でない同一Sが複数回現れる区間を探し、指定個数の断片を作る。まず保護する区間の長さを最大化し、次に同じ長さならSの要素数を優先する。内部の分割点は最大断片長を最小化する動的計画法で選ぶ。異なる型列をdummyで埋めない。

全断片はS→Sになる。各caseをSを結果に持つblockで囲み、loopはSと次stateのi32をparameterとして受け取る。br_tableはstateを消費し、Sをcaseへ直接渡す。断片末尾はSに次stateを積んでloopへ戻り、最後はSで外側blockを抜ける。PC用localもstack spill用localも追加しない。prefix/suffixは順序を変えずに実行する。

比較用には、全く同じ分割点・case配置・次stateを使い、Sをlocalへ退避して復元する通常のdispatcherを作る。型や分割点の違う対照から有利さを作らない。候補の差分は分割点選択と受渡し構成であり、単に未知の数学原理を求めるものではない。

## 先行研究

WASMixer (Cao, He, Guo, Wang, 2023 arXiv v1), https://arxiv.org/html/2308.03123v1 の§4.2.1/Algorithm 2/3を確認。分割境界でstackを追加localへ退避・復元し、loop/switchで再配置する方式が近い。著者実装の同条件実行は今回まだない。

multi-value block/loop parameter自体はWasmの既知機能で、SSAのblock argumentとして理解できる。以前のnullable/non-null初期化対照で単純なtyped payloadの優位性が出なかったことも保持する。今回の対象は非nullable参照の初期化ではなく、数値スタックの同じ型列を反復する分割点の選択である。ただし一般のSSA/stack allocation研究から独立した貢献かどうかは未確定。

セルオートマトンの初期配置へプログラムを移す方向も検討したが、CookのRule 110コンパイラ（https://arxiv.org/abs/0906.3248、今回は要旨のみ確認）が既に存在する。具体的に異なる構成と費用の見通しがないため、単なる移植の試作を先行させない。CA方向全体を不可能と判断したものではない。

## 意味保存と範囲

単一のdefined functionの直線命令列を最初の実装範囲にする。数値演算、local、選んだscalar load/storeを扱う。元の副作用とtrapし得る命令の順序は変えない。新しい制御は確定したstate列だけを実行する。ホストからmemoryを読める場合と、trapした後のmemoryも照合する。sourceのif/loop、call、GC、SIMD等を未対応として明示する。

## 評価する仮説

同じ保護区間と同じdispatcherの対照に対し、stackの退避・復元を省くことでサイズや実行費用を減らせるか。解析耐性が強くなるとは先に仮定しない。元の順序の復元に対し、型とbranch payloadを追う方式既知の解析がどの費用で成功するかを測る。復元可能性だけを棄却理由にしない。

staticなstate列を部分評価すれば両方式とも平坦化前の直線処理へ戻る可能性が高い。この対照を省略せず、単なる既存平坦化の省サイズ実装に留まるなら、その範囲を明記する。Wasm最適化後の未対応を保護効果と数えない。
