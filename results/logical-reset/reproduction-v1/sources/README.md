# J：論理容量とセグメント寿命によるWasm再初期化

2026-10-24。**動作するバイナリ変換と限定実験はあるが、特許につながる新規性は未確立。** 詳細は[構成・請求項案と先行対比](novelty-analysis.md)。修士研究との両立を考え、core Wasmの狭い意味保存問題として実装した。

同じinstanceを再利用し、guestが見る容量とsegmentの有効長をprivate stateで管理する。成長後の領域や破棄segmentを扱いながら初期状態へ戻す。元codeのmemory/tableアクセスも論理容量で検査するため、内容をコピーするだけのresetとは動作が異なる。

Node 25,704比較、Wasmtime 8,148比較でfullの不一致0。不完全3方式には各反例がある。Nodeのcached Moduleからfresh instanceを作る対照より速いが、runtime poolingとの比較は未実施。第三者コーパスの非空219本は現状のinterface制約で全て対象外だった。[実測と限界](results.md)

## ファイル

- [事前計画](plan.md)、[アルゴリズム・意味保存条件](algorithm.md)、[先行技術と読了範囲](prior-art.md)
- [請求項たたき台・新規性仮説](novelty-analysis.md)、[実験結果](results.md)、[日本語研究ノート](paper-note.md)
- [変換器](prototype.py)、[fixture](fixtures.py)、[Node差分試験](run.cjs)、[Wasmtime差分試験](cross.py)
- [性能入力の統一](bench-inputs.py)、[性能測定](bench.py)、[対応外の拒否](boundary.py)、[コーパス早期除外](corpus-screen.py)

## 環境と実行

リポジトリrootを作業directoryにする。Python 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133、Wasmtime Python 50.0.1を使用。toolの既存配置は `.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`、`.tools/import-alias-quotient-python`。AST readerを `research/connectivity-elimination/prototype.py` から共有する。これらのpathsを変更する場合は共有moduleの定数とcross.pyの検索pathを合わせる。再現スクリプトは依存を自動downloadしない。

```powershell
python research/logical-reset/prototype.py input.wasm output.wasm
python research/logical-reset/reproduce.py results/logical-reset/reproduction-local
```

新しい出力先を使う。既存出力へ上書きしない。`--mode full`が通常変換で、plain/no-bounds/no-dropは誤実装の実験用対照である。

一括再現はfixture生成→validate→Node raw/O3比較→Wasmtime比較→境界拒否→APIを揃えた性能入力生成→5process性能測定を行う。declarative segmentに関するBinaryen拒否はmanifestへ分離する。再現時間や性能値は環境で変化する。保存済み結果のhashを読むだけで再実行したことにはしない。

```powershell
# 任意：手元の取得済みコーパスの静的な適用範囲検査
python research/logical-reset/corpus-screen.py .tools/nowaset-53118203 results/logical-reset/corpus-screen-local
```

閉じたmodule、private bounded memory32、任意のprivate funcref table、数値APIが前提。imports/start/state export/shared memory等は非対応。resetはtrusted hostがguest停止後に呼ぶ。初期化途中・実行中の復元、任意のWASIアプリの再利用、hostの残留memory読取りへの保護は対象外。全入力を証明したものではない。
