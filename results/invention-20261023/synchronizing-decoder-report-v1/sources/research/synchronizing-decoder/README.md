# synchronizing-decoder

2026-10-23。非可逆な状態遷移と算術の重みを使い、異なる入口の解釈状態を同じ結果へ収束させる限定Wasm変換器。**主発明には不採用。** 重み付き同期が既知であり、方式既知の代表状態解析でも回復できた。

[事前計画](plan.md)、[アルゴリズムと証明の範囲](algorithm.md)、[先行研究・既読範囲](prior-art.md)。実測は `results/invention-20261023/synchronizing-decoder-*` に保持する。

元Wasmのifを維持し、x+a*y+bを4/8状態のhelperへ置換した。任意CFG全体で解釈状態を持ち回るコンパイラや、汎用VMではない。3種のARX入り人工kernel、raw/O3、fixed/sync、負の重み対照を比較する。単なる状態数の変更を複数の発明に数えない。

主54正条件62,208呼出しは一致。代表状態だけの追試12条件13,824呼出しも一致し、全状態解析の回復binaryとbyte一致した。負対照12条件は全て誤答を検出。96gateの係数証明・加算potentialへの反例、縮小幅9,216組、WABT324呼出し、24回復binaryの再生成一致を確認した。

性能は63 fresh process・441batchで測定。syncは元の約3.71–30.80倍の実行時間となった。全入口の検証には状態数に比例する増分があったが、代表から候補を生成する費用はfixedと近い。この二つの解析課題を混同しない。

## 再現

Python3.9.0標準library、Node24.15.0、WABT1.0.42、Binaryen133を使用。`.tools`の既存配置と `research/isotope-swizzle/prototype.py`、`research/connectivity-elimination/prototype.py`、`research/span-mask/bench.cjs` が共通依存。Windows 10.0.26100 x64で実行した。

repository rootで、未作成の出力ディレクトリを指定する。

```powershell
python research/synchronizing-decoder/run.py results/reproduce-sync-main
python research/synchronizing-decoder/followup.py results/reproduce-sync-main results/reproduce-sync-representative
python research/synchronizing-decoder/audit.py results/reproduce-sync-main results/reproduce-sync-audit
python research/synchronizing-decoder/performance.py results/reproduce-sync-main results/reproduce-sync-runtime
```

単一変換は `prototype.py INPUT.wasm OUTPUT.wasm --n 4 --mode sync`。`fixed`は入口状態を固定するアブレーション、`bad`は試験用の誤変換。回復は `recover.py INPUT.wasm OUTPUT.wasm`、代表候補だけの生成には `--representative` を付ける。後者は同期の約束に依存し、未知binaryの一般同値証明ではない。

性能測定は16,384回warmup、20ms較正、各条件3process×7batch。core O3後に同じWasm loopを付加し、V8では `--no-liftoff --no-wasm-lazy-compilation` を使用。回復coreへ追加O3なし。CPU affinity・外乱制御なし、RSSはNode全体。helper由来のmemoryは1pageで、元/回復はmemoryなし。主解析時間は各条件1回であり、費用の厳密な統計的比較とは扱わない。

v1はO3によるrem_u→andの変更を回復器が未対応として拒否し、未完了。対応を加えたv2が完了記録。さらに代表解析・拒否条件の厳密化を追加した現コードで24回復を再生成し、byte一致を確認した。保存した集計時のソースと主測定時のログ項目は一部異なることを明示する。未対応、parser不備、推測だけの困難さを耐性の成功に数えない。
