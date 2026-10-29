# 再開研究：可変関数テーブルによる制御状態の移送

2026-10-18。前回の式再合成は終了した研究区間として保存し、本目標はactive。最初のターンは新しい設計と反証用実装へ進む。前回は実装・測定・成果物を保存したためprogressである。

## 仮説と具体的規則

前回の公開多項式・固定した中間式の再構成から離れ、Wasmの実行時可変funcref tableとbulk table.copyを使う。候補は、整数dispatcher状態qを保持する代わりに、テーブルTの先頭に現在の処理の参照を置く。全処理は同じ(i32)->i32型を持つ。Nは2の冪。

元：x←f[q](x); q←(q+d(x)) mod N。

変換後：x←call_indirect T[0](x); T←rotate_left(T,d(x))。

初期T=[f0,...,f(N-1)]。N個のscratch slotを使い、全体の退避、末尾の先頭へのcopy、先頭の末尾へのcopyという3つのtable.copyで回転する。呼出しごとにpassive element segmentから初期化する。

不変条件T[i]=f[(q+i) mod N]から局所・反復の意味一致が説明できる。前提はprivate table、外部importなし、再入なし、全stepが純粋でtrapしないこと、全間接呼出しが正しい型・範囲内であること。公開table、共有table、任意の関数参照比較や外部状態へ一般化しない。

## 何が新しい可能性を持ち、何が既知か

静的なcall→call_indirect置換と違い、calleeを選ぶ整数値を使わずテーブルの配置が変化する。Wasmはcodeが不変でもtableを変更でき、table.copyは参照を数値化せず移動できる。ただしdispatcher表の変更・置換自体は既知であり、Wasm命令への移植を新規性としない。

一次資料：WASMixerのalias disruption（[本文](https://arxiv.org/html/2308.03123v1)）、[Wasm table実行規則](https://webassembly.github.io/spec/core/bikeshed/)、[bulk table操作の提案](https://github.com/WebAssembly/spec/blob/main/proposals/bulk-memory-operations/Overview.md)。さらに[Multiple instruction dispatch tables for application program obfuscation](https://patents.google.com/patent/US7353499B2/en)を検索で発見した。特許は査読論文ではなく、法的な実施判断を行う資料として使わない。複数dispatcher表・命令位置置換という広い主張の先行例として扱う。本文全手順との同一性は未精査。

検索語：WebAssembly obfuscation table.copy / table.set dynamic / obfuscation permutation dispatch table / self-modifying function table。検索結果に同じ名称がないことを新規性の証拠にしない。

## 先に試す適応的解除

この回転族にはqという小さい商が残る。初期配置と3copyの効果を公開バイナリから認識できれば、回転量の累積qだけを追い、table[0]の呼出しを元の固定table[q]へ戻せる。反復回数や入力を列挙する必要はない。これが自動的に成功するなら、この規則を採用しない。

解析者には変換方式とWasmだけを与え、元バイナリ・生成時の状態表は渡さない。原理上の還元と実バイナリからの認識を区別する。O2/O3の認識が未対応なら、その状態を耐性の成功にしない。

## 固定した初期実験

N=4/8/16、語回転・xor・乗算を含む純粋なstep関数、0–63反復の入力依存状態遷移。元の静的table版、輸送版、解除版を同じ入力・raw/O2/O3で比較する。実.wasmを入力する限定変換CLIを作る。境界値と固定seedの乱数で反復呼出しを検査し、バイナリサイズ・処理時間を記録する。成功条件はvalidationだけではなく、方式既知の商への還元後にも残る有用な差である。

これは採用候補を確定した計画ではない。回転を一般置換へ改名しただけで別案と数えない。今回の小さい商を避ける独立した規則が必要で、現段階では定義されていない。
