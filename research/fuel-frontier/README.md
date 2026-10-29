# F: 公開イベントに沿う累積fuel予約

2026-10-24。Wasmセキュリティ全般へ広げた研究の追加候補。Aの権限受付、Bの旧値view、Cの資源返却とは別に、**途中の予算停止が秘密の計算量を漏らす問題**を扱う。限定バイナリ変換と実験は完了したが、特許の主案としての新規性は未確立。

- [アルゴリズム・請求項F1–F4](algorithm.md)
- [攻撃モデル](threat-model.md)、[先行調査](screening.md)、[新規性の反証](novelty-analysis.md)
- [実験結果と失敗記録](results.md)、[日本語草稿](paper-draft.md)
- [初期計画](plan.md)、[公開値を伴う修正計画](release-plan.md)、[性能計画](release-performance-plan.md)

入力は`.wasm`。PythonでWABTの検証済みfolded WATを読み、非巡回の限定命令列について公開event列と累積費用を求め、予約callを挿入する。出力は標準Wasmで再検証する。総量だけ末尾で揃える対照、全関数予約、区間別予約、手書き同一予約と比較する。

## 再現

リポジトリルートのPowerShellから実行する。出力先は既存でないディレクトリを指定する。過去の結果は上書きしない。

```powershell
python research/fuel-frontier/probe.py results/fuel-frontier/repro-probe
python research/fuel-frontier/audit.py results/fuel-frontier/repro-audit
python research/fuel-frontier/release.py results/fuel-frontier/repro-release
python research/fuel-frontier/cfg-audit.py results/fuel-frontier/repro-cfg
python research/fuel-frontier/release-performance.py results/fuel-frontier/repro-release results/fuel-frontier/repro-performance
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python research/fuel-frontier/wasmtime-check.py results/fuel-frontier/repro-release results/fuel-frontier/repro-wasmtime
```

単独変換例:

```powershell
python research/fuel-frontier/transform.py results/fuel-frontier/release-v6/rust-2-O3-flat.wasm results/fuel-frontier/demo.wasm --mode frontier --release-values --acyclic
```

Python 3.9、Node 24.15.0 / V8 13.6.233.17、WABT 1.0.42、native Binaryen 133を使用。WABT/Binaryenは`.tools/`、探索helperは`research/connectivity-elimination/prototype.py`に依存する。Rust例はrustc 1.97 nightlyとmatching sysroot/linkerを`.tools/masters-security-rust/toolchain.json`から読む。独立配布パッケージではなく、このリポジトリと記録したtoolchainを使う。`results/*/sources`は当該実験のsource snapshotであり、単独で移動実行できるpackageではない。

対応範囲はi32の非trap整数演算、local、定数idのmarker、void if。`--acyclic`ではvoid block、値なしbr/br_if、folded returnも受理する。`--release-values`はmarkerの第二引数を明示公開値として許す。loop、memory/globalアクセス、一般call、再帰、浮動小数、threads、例外、Componentは未対応。未使用のmemory/global定義は保存する。細部は実装のsubset検査を正とする。

費用は**入力バイナリの論理opcode数**であり、runtime固有fuel、実時間、host内部費用ではない。性能測定の後段最適化によってこの会計単位を変更しない。

## 現在の判断

公開値付きRust最適化例では、区間独立予約167を累積予約99へ減らした。同じ公開出力の入力対について予算由来の差がないことを検査した。正しい全関数予約・手書き予約も安全であり、手書きより生成版は約17～23%遅い。例は自作で実アプリ導入効果は未確認。定資源型・イベント予定・gas privacyが強い先行技術で、技術的効果と特許新規性を分けて扱う。
