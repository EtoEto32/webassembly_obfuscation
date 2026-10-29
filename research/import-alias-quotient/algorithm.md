# Gの構成と意味保存条件

本方式は境界構成を比較する検査器であり、memory safetyを追加する防御器ではない。実験後、統合変換は既存のwasm-mergeで実現できると分かったため、主発明としては不採用。

## 手順

入力: 標準Core Wasm M、同じmemory32 limitsを持つn個のmemory import、実object同一性partition P。

```text
validate M; reject unsupported instructions and module constructs
require P is a restricted-growth string of length n
representatives = first index of each P class
for each memory instruction, active data target, memory export:
    rewrite memory index i to P[i]
keep one import declaration for each class, retaining its original name
keep all data segments in their original order and keep data indices unchanged
validate quotient Q

instantiate M with repeated Memory objects according to P
instantiate Q with one corresponding Memory object per class
compare return/trap and physical-memory state after every call
```

Wasmのmodule indexからstore内memory addressへの対応をρ、商側をρ′とすると、`ρ(i)=ρ′(P[i])`が不変条件になる。各load/store/fill/copy/init/growは同じstore objectを参照し、同じ順で状態遷移する。特にmemory.copyの二つのindexが違ってもstore addressが同じ場合の重なりを保持する。active dataの初期化順、data.drop状態、trap前に完了した副作用も維持する。

これは限定subsetに対する紙上説明であり機械証明ではない。allocation failureの非決定性まで等しくする保証ではなく、試験は各1～3pageに制限する。host callback、再入、threads、memory64、異なるlimitsの統合を扱わない。元の異なるobjectを勝手に同一視する変換でもない。

## 検査する脅威

コンパイラや境界生成器が、異なるmemory indexを根拠に非aliasと誤って扱う場合の返値・副作用の差を検査する。攻撃実装やsandbox escapeの実証ではない。hostが渡すobjectの同一性をテスト入力の一部にする。

## 請求項たたき台と反証

**G1**: WebAssemblyの実行境界を検査する方法であって、複数のmemory importへ供給するmemory objectの同一性分割を生成し、前記分割に従い複数importを同じobjectへ結合した第一実行と、memory indexを同値類へ写し重複importを除いたmoduleの第二実行を構成し、命令終了及びtrap時の返値と各物理memoryの状態を対応付けて比較する方法。

**G2**: G1において、active dataの順序及びpassive dataの識別子を保持し、memory.copyの同一object内重なりとmemory.growの共有サイズ変化を比較対象に含める方法。

**G3**: G1において、変換前後に標準validationを実行し、同一性分割と初期memory内容を固定した複数呼出し列で比較する方法。

**G4**: G1において、独立した実行模型又は異なるruntimeの結果をさらに照合し、変換器の誤りと被検査runtimeの差を切り分ける方法。

これらは技術要素の記録であり、成立性確認済みの請求項ではない。**wasm-merge + alias re-export wrapperが198条件全てで同じ観測を得た**ため、index統合を独自なアルゴリズム要素として主張しない。検査用途への転用だけでは進歩性の根拠が弱い。
