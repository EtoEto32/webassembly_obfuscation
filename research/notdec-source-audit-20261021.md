# NotDec実装から次の変換仮説を絞る

2026-10-21。公開リポジトリを作業領域内 `.tools/notdec-source` に取得。外部公開・pushは行っていない。固定コミット：`0399bf0aec0f26247fee99097cb9442e4414bb0f`。submoduleは未取得、ビルド・逆コンパイルは未実施。取得しただけで比較実験が済んだとはしない。

## 実装で確認したこと

- `src/CMakeLists.txt` は `TypeRecovery/PointerNumberIdentification.cpp` を組み込む。似た名前の `TypeRecovery/mlsub/PNDiff.cpp` はコメントアウトされている。ファイル名だけで実行される解析を決めない。
- `PointerNumberIdentification.cpp` の `matchOffsetRange` はAdd/Mul/Shlを再帰的に扱い、それ以外を未知の変動アクセスへ落とす。`matchOffsetRangeNoNegativeAccess` は負のSizeを持つaccess要素を除く。これはこの関数の挙動であり、最終的な構造体回復が必ず失敗するという観測ではない。
- `ConstraintGenerator.cpp` の `addCmpConstraint` は両operandのPN変数をunifyする。`visitICmpInst` はこの関数を呼び、ここには比較predicateによる条件分岐がない。論文の等値比較の説明だけから実装の全挙動を推測せず、呼出し前の最適化も考慮する必要がある。
- 同ファイルの命令型表にはXor/Mul/Shl/LShr/AShrの数値制約がある。これらを経由してpointerを生成するだけの案は、数値制約へ衝突を作れても、通常の算術正規化で戻る可能性がある。

[固定版コード](https://github.com/NotDec/NotDec/tree/0399bf0aec0f26247fee99097cb9442e4414bb0f)、[論文§3.2](https://arxiv.org/html/2608.03286v1)。今回論文ではPNDiffの規則表、制約生成、関数間伝播、Memory SSAの説明を確認。全実装を監査したとはしない。

## 環境の確認結果

`docker info`：Docker Desktop Linux engineのnamed pipeがなく接続不能。`wsl --list --quiet`：通常sandboxではE_ACCESSDENIED、読み取り専用の権限付き再実行は成功し、`docker-desktop`のみ列挙された。これは自動承認拒否ではなく、最初の実行環境のアクセス制約だった。

Git cloneもsandbox内では名前解決用threadの開始に失敗し、権限付き再実行で成功。READMEはUbuntu22.04/LLVM14、現在のCMakeの既定パスはllvm-14.0.6.obj。一方、既存DockerfileはLLVM13で、READMEと一致しない。既存Dockerfileをそのまま最新再現環境と扱わない。CMakeはPATHに見つからなかった。これらはNotDec実行の準備事項であり研究全体の停止理由ではない。

## 次の設計に対する具体的な判定

|仮説|狙う情報|最短の反証|現時点の扱い|
|pointerとnumericの比較を共有し型分類を混同させる|PNクラス|比較の用途別分離、算術正規化。特定実装の制約不足に依存し得る|これだけを発明にしない|
|基点を配列末尾へ移し負strideでfieldを参照する|offset/array境界|符号付きaffine正規化で基点を戻す。配置変換の既知性も強い|単独候補にしない|
|異なる用途の値を共有関数へ通し、呼出し文脈を増やす|関数間field対応|引数位置summary。過去typed-relayでも弱かった|再試行しない|

型回復の規則を一つ外すことと、方式既知の解析に継続した費用を課すことは違う。次の実装候補には、通常のaffine変換や用途分離を施した後にも保護対象の復元へ追加作業が残る具体規則が必要。この条件を満たす方式はまだ確定していない。NotDec未実行のため勝敗や失敗率は記載しない。
