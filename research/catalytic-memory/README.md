# 内容不明のメモリを借りる計算：早期反証

2026-10-23。実Wasm生成・方式既知の回復・trap後の状態を検証した。**この構成は主特許候補に採用しない。** 未知の作業領域は秘密ではなく、計算結果からその依存を消せる場合は通常コードを回復できる。

[事前計画](plan.md)、[実装](gate.py)、[主結果](../../results/invention-20261023/catalytic-memory-gate-v2/checks.json)、[回復記録](../../results/invention-20261023/catalytic-memory-gate-v2/manifest.json)、[独立監査](../../results/invention-20261023/catalytic-memory-audit-v1/audit.json)。

## 原理と範囲

任意の初期word cに対して、`c+=x; r=c*y; c-=x; r-=c*y`はcを復元し、r=x*y mod 2^32を得る。加減算をXOR、乗算をANDとするとANDについても成り立つ。Wasmのwrap整数で正確に成立するが、恒等式そのものは新規と主張しない。

変換器は既存`.wasm`を読み、1pageの上限付きmemory、2または3個のi32引数、export `run`を持つ限定例を変換する。元関数は積・AND、またはその結果を第3引数でunsigned除算する形だけ。元memoryは関数から参照されず、先頭wordを借りる。memoryはexportされるため、終了・trap後の変更は観測可能。imports・共有memory・他の関数・可変アドレス・一般プログラムは対象外。新しいメモリを増設せず、既存の1pageを借りる。

## 解析

公開binaryをWABTで読み、operand stackと1wordのmemory SSAを追う。算術はZ/2^32の多項式正規形、bit演算はBoolean ANFで簡約する。最終memoryと各trap点のmemoryが初期値に等しいことを検査し、出力に初期値が残らなければ通常のWasmへ出力する。元式は回復入力に使わない。強い全入力条件で確認するので、この限定familyでは意味保存の根拠を説明できるが、解析器の実装全体を証明したとは主張しない。

途中で除算してからmemoryを戻す負例は、通常終了では値が合ってもゼロ除算後にmemoryが壊れる。raw/O3双方で初期305419896が305419903に変化した。回復器は両方を`trap_memory_changed`として拒否した。正常終了だけのテストはこの差を見落とす。

## 結果

3例×元/借用/回復×raw/O3の18条件、76,374呼出しで値・先頭wordの不一致0。期待したゼロ除算trap3,366件を含む。他のmemory領域も照合した。独立WABTで72呼出しと72状態照合、3生成byte replayが一致した。回復は借用版6/6、coreの正規化は約0.056～0.080ms、WABT読取を含む前処理は約17.3～18.2ms。単回観測であり分散を測っていない。

O3サイズは元版56/56/60bytes、借用版96/96/100bytes、回復版56/56/60bytes。変換は約38ms（コンパイル・validation込み、単回）。既存memoryは全版65,536bytes。独立した新規性と解析増分が見込めないため、実行時間/RSSの本測定はしていない。span-maskの性能測定とは区別する。manifestの`recoveries[].bytes`は回復後サイズで、入力サイズは`targets`にある。

初期v1はfolded WATを完全な二分木と誤認したreaderがIndexErrorで停止した。storeをまたぐoperand stackを正しく扱うよう修正し、v2で全件再実行した。[失敗記録](../../results/invention-20261023/catalytic-memory-gate-v1/failure.md)を残し、ツールの不備を保護効果に数えない。

## 近い先行技術

Craig Gidney, [Factoring with n+2 clean qubits and n−1 dirty qubits](https://web.physics.ucsb.edu/~martinisgroup/papers/Gidney2017.pdf), arXiv:1706.07884v1, 2017。今回読んだ版はプレプリント。abstractと§1に、任意状態のdirty ancillaを借りて戻す古典可逆回路という目的が明記される。全回路や量子因数分解の評価を再現したものではない。

Wasmへの実装とtrap条件の明示はできたが、既知の可逆計算を超える生成原理は示せていない。最大のReject理由はこの近接性と、memory依存を小さな正規化で除去できる点である。

## 再現

span-maskと同じPython/Node/WABT/Binaryen配置。リポジトリrootから、未使用の出力先を指定する。

```powershell
python research/catalytic-memory/gate.py transform input.wasm output.wasm
python research/catalytic-memory/gate.py recover output.wasm recovered.wasm
python research/catalytic-memory/gate.py run results/replay-catalytic
python research/catalytic-memory/audit.py results/replay-catalytic results/replay-catalytic-audit
```
