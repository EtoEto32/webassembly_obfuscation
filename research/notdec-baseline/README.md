# 型回復評価用の基準入力

2026-10-21。難読化方式ではなく、NotDec等の実ツールによる比較に必要な未変換基準。前turnはNotDecのソース取得・調査によりprogress。本turnは依存ソース取得、実行環境診断、基準Wasmの生成・テストを行った。

## 入力と正解

`fixtures.py` は線形メモリ内の単方向連結リストを生成する。レコードは12byte、next/key/valueは各32bit、基点64。8/32/128レコード×3フィールド配置＝9モジュール。各サイズのキーと値は配置間で共通なので、9個の独立データ集合とは数えない。memoryは非export、公開API `lookup(key)` は一致するvalueまたは0を返す。0は保存valueに使わない。

全保存キー、境界4入力、固定seed乱数512をNodeで照合し、合計5,148呼出しが一致。WebAssembly.Moduleによるバリデーションも通過した。全入力証明ではない。公開lookupがあるため値の秘匿性を評価するベンチマークにはしない。

```powershell
python research/notdec-baseline/fixtures.py results/notdec-baseline-replay
```

[入力hash・フィールド正解・照合件数](../../results/invention-20261021/notdec-baseline-v1/manifest.json)。同じ出力ディレクトリへの上書きを拒否する。

## 評価時に区別する項目

1. 実ツールが正常終了してCを生成したか。
2. 生成Cが再コンパイルでき、同じlookup結果を返すか。
3. nextをレコードへの参照として、key/valueを32bit値として回復したか。
4. 三つのフィールドのoffsetとstrideを正しく区別したか。

構文名は採点しない。型名を付けただけで回復成功としない。正しいがbyte配列のままの出力は実行成功・構造回復未達と分ける。未対応・クラッシュ・時間上限・誤答も別集計する。正解manifestを逆コンパイラへ渡さない。現時点では**NotDecによる1–4の測定は未実施**。

## NotDec実行環境の状態

本体commit `0399bf0aec0f26247fee99097cb9442e4414bb0f`。
取得済みsubmodule：llvm2c `316dfbbf9bb12c4ddad300ab01036e616b23f229`、wasm2llvm `c3c2c189f5aaa66c2f211bc3b8b7dbe34e1ee696`。WABT1.0.33をビルド時取得する設定。LLVM14/Clang開発ライブラリ等の環境はまだ構築していない。

Docker Desktop起動を試したが、2026-10-21 04:17:39 UTCのbackendログは `initializing Inference manager` の `dockerInference` ソケット初期化で異常終了したと報告。45秒指定のstart CLIは終了せず、infoも待機した。起動済みプロセスとログを確認した後、今回のCLIプロセスだけを終了し、両ツールsessionがexit 1になったことを確認。factory reset、Docker設定変更、コンテナ・データ削除は行っていない。これはNotDecの解析失敗ではない。Desktop GUIのエラー状態が残る可能性はある。

全研究が停止しているわけではない。未対応を効果に数えず、実ツールの準備と発明仮説の検査を分けて継続する。

## 2026-10-23のread-only再確認

Docker infoはdockerDesktopLinuxEngineのpipe不在で終了。WSL一覧はsandbox内でE_ACCESSDENIEDだったが、承認されたsandbox外の同じ一覧取得ではdocker-desktopのみを返した。通常のLinux開発環境を得たことやNotDecの実行成功を意味しない。Docker/WSL設定変更、再インストール、factory resetはしていない。研究全体は別の仮説検査を継続している。
