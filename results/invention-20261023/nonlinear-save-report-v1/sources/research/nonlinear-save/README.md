# nonlinear-save

Wasmの非線形メモリ表現について、copy列のどこでtrapしても修復できる共通の退避codeを生成する試作。4bit全状態を列挙し、二つの情報損失階層から最適彩色とclique証明を同時に得る。原理に強い先行研究があり、主たる難読化発明には採用していない。

[設計・証明・対応範囲](algorithm.md)、[先行研究と既読範囲](prior-art.md)、[実装前の計画](plan.md)。実験の生値は `results/invention-20261023/nonlinear-save-*` に保存する。

## 得られた結果

探索600例中1例で最良線形保存2bitに対して1bitとなった。独立に分けた600例でも1例で同じbit削減があり、その例も実Wasmで正当性を確認した。一般的な50%削減とは言えない。全8!通りの3bit bijectionを一つのcopy列で調べた40,320例ではbit削減は0件だった。

主42条件40,362 API呼出しと追試14条件12,614呼出しは一致し、負対照8条件は全て反例を検出した。WABTの別実行器でも42条件・420runが一致した。方式既知の回復器は全24変換条件について有限状態profileの同等プログラムを生成した。回復結果を元ソースの一意な復元と扱わない。

主の改善例ではrepair表192→96byte、全表240→144byte、O3バイナリ649→606byte。saved localはどちらもi32一つ、メモリはどちらも65536byteである。実行時間に明確な改善はない。補助的な生成技術の効果を解析耐性や実メモリ半減と混同しない。

## 環境と再現

Python 3.9.0、Node 24.15.0、WABT 1.0.42、Binaryen 133を使用。外部Python packageは不要。リポジトリ内の `.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin` を共通helperが使う。Windows 10.0.26100 x64で測定した。

全てrepository rootで実行する。出力は上書きしないので未作成のディレクトリを使う。

```powershell
python research/nonlinear-save/model.py results/reproduce-ns-screen
python research/nonlinear-save/run.py results/reproduce-ns-screen/screen.json results/reproduce-ns-main
python research/nonlinear-save/audit.py results/reproduce-ns-main results/reproduce-ns-audit
python research/nonlinear-save/holdout.py results/reproduce-ns-audit/holdout.json results/reproduce-ns-holdout
python research/nonlinear-save/performance.py results/reproduce-ns-main results/reproduce-ns-runtime
```

単一の入力には `prototype.py transform INPUT.wasm OUTPUT.wasm --encoding E.json --mode color` を使う。E.jsonは0..15の置換配列。`--mode full`、`linear`が対照であり、`bad`は故意に誤動作させる試験専用。`prototype.py recover INPUT.wasm OUTPUT.wasm` は公開APIだけを利用する回復器。

性能測定は3独立process×7batch、warmup16,384、20ms較正、Nodeの `--no-liftoff --no-wasm-lazy-compilation` を共通に設定する。normal pathのみでreset/run/peekと共通Wasm loop全体を測る。全315batchは10ms以上。CPU affinity・外乱制御なし。RSSはNode全processの指標である。

最初のaudit-v1はWABTの正常void出力を拾う正規表現に不備があり、未完了記録を保持した。修正後audit-v2が完了記録である。このログ処理不備は変換の反例でも保護成功でもない。任意Wasm、実アプリ、他の逆コンパイラの評価はこの追試では行っていない。
