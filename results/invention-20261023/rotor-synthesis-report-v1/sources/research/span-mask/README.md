# 入力依存の線形包表現

2026-10-23。動作するWasm変換と適応解析まで実装したが、**新規性と保護費用の双方から主特許候補には不採用**。元計算の式や生成時の変換列を配布せず、入力依存の行列の線形包判定へ置換する試作。既知のspan program、入力依存の可逆行列生成を新発明とは扱わない。

- [事前計画と3原理候補](plan.md)
- [アルゴリズム・意味保存・攻撃モデル](algorithm.md)
- [先行技術との対応](prior-art.md)
- [保存結果の自動集計](../../results/invention-20261023/span-mask-report-v1/report.md)
- [日本語の研究ノート](paper-note.md)

## 再現

Windows、Python 3.9、Node 24.15.0 / V8 13.6.233.17-node.48。WABT 1.0.42を`.tools/wabt-1.0.42/bin`、Binaryen 133を`.tools/binaryen-version_133/bin`に配置する。Python標準ライブラリのみ。共通parser/BDDを`research/connectivity-elimination`から読み込むため、リポジトリ全体を用いる。外部サービス・秘密鍵は不要。

リポジトリrootで、新しい出力先を指定する。既存結果は上書きしない。

```powershell
python research/span-mask/prototype.py input.wasm output.wasm --mode dependent --seed 20261023
python research/span-mask/run.py results/replay-span-main
python research/span-mask/io_attack.py results/replay-span-main results/replay-span-io
python research/span-mask/peel.py results/replay-span-main results/replay-span-peel
python research/span-mask/performance.py results/replay-span-main results/replay-span-io results/replay-span-runtime
python research/span-mask/audit.py results/replay-span-main results/replay-span-io results/replay-span-peel results/replay-span-runtime results/replay-span-audit
python research/span-mask/report.py results/invention-20261023 results/replay-span-report
```

最後のreportコマンドは保存済みの`span-mask-*-v1`を集計する。新しいreplayの名前を集計する場合はreport.pyの入力名も合わせる。Node実行flags、warmup、反復、seed、攻撃の上限は各スクリプトに固定し、結果の`sources/`にも当時のコードを保存した。実験中に測定コードを変更していない。

入力は1関数、export `run`、1～32個のi32引数、i32結果、AND/OR/XORと0/-1と引数参照のみ。imports・元memory・trap演算・float・任意のC/Wasmは対象外。列数64、行数96、係数データ512KiBなどの生成上限もある。評価3例は各1ページのprivate memoryを使用する。命令の一般性を過大に主張しない。

## 得られたこと

主検証158,558呼出しで不一致0。追加Node45,056、scratch6,144、WABT164呼出しと独立GF(2)モデル1,152入力も一致した。raw/O3の直接・前処理BDDでは36条件中26復元・10node上限。適応的な全数入出力学習ではO3の12条件全て同等Booleanコードを復元した。24入力の入力依存版は524,288回のpacked問い合わせ、問い合わせ部分約22秒。これは「解析できない」という主張を否定する結果である。

入力依存版は固定混合版より約3.8～11.4倍遅く、元版との差はさらに大きい。残る先行技術との差が小さいうえ、実用的な費用対効果を示せていない。有限環方式の従来の限定した構成候補は別に保持する。
