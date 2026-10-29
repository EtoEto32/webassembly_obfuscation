# Wasm復元診断：小さな再現パッケージ

2026-10-24。公開resourceへのhost書込みによって診断契約が変わることを、元exportだけの小例、Node/Wasmtime、別array式、CLIで再現する。新しい一般的検証原理を主張するartifactではない。imports、動的operand、grow、shared state等を扱う一般Wasm解析器でもない。

含むもの：条件合成器、公開書込みの反例生成、必要なparser、6 controlsと2 interleave programの生成器、2engine照合、Z3による44義務の検査。巨大な旧研究履歴、第三者復元器、外部ツールbinary、アカウント情報は含まない。公開・配布操作は行っておらず、local review用である。

## Windowsでの準備

実測環境は64bit Python3.9、Node24.15.0、WABT1.0.42、Wasmtime50.0.1、Z3 4.13.3.0。現行ツール呼出しが`.exe`を使うため、Linux/macOSでそのまま動くとはしていない。

[WABT公式release](https://github.com/WebAssembly/wabt/releases/tag/1.0.42)のWindows packageを取得し、`wat2wasm.exe` / `wasm2wat.exe` / `wasm-validate.exe`が`.tools/wabt-1.0.42/bin/`に置かれるよう展開する。NodeはPATHへ置く。Python依存はpackage rootで次を実行する。global環境へのinstallは必要ない。

```powershell
python -m pip install --target .tools/import-alias-quotient-python wasmtime==50.0.1
python -m pip install --target .tools/encoding-synthesis-python z3-solver==4.13.3.0
python reproduce.py
```

[Wasmtime package](https://pypi.org/project/wasmtime/50.0.1/)、[Z3 package](https://pypi.org/project/z3-solver/4.13.3.0/)を指定している。依存コードのlicenseは各packageのものに従う。このartifactは依存binaryを再配布しない。

既に依存がある場合は、`WASM_TOOLS_ROOT`をそれらの`.tools` directoryへ、`PYTHONPATH`をWasmtimeとZ3のinstall先へ設定してもよい。これは外部ツールの共用だけで、研究sourceはこのpackage内から読む。再現器はparserのrootがpackage自身であることをassertする。

## 期待する結果

`results/state-witness/reproduction.json`に`passed`、9個の再生成binaryのbyte一致、44個のUNSAT義務を記録する。controlsは36契約中32契約を元exportから実行し、観測できないprivate/fullの4契約を実行済みに数えない。両engine各274 guest API呼出し・272状態準備呼出し・48cell書込みで一致する。

interleave例では、外部書込みがないと任意の共通初期storeで公開観測が一致する。しかし `arm → 公開tableを書換え → publish` の3操作では差が出る。初期条件だけを閉じる方法ではこの例を検出できない。修復版とtrap終端契約は一致する。二つのengineで各12診断call・8準備call・4cell書込みを検査する。

既存の出力は上書きしない。再実行はarchiveを新しいdirectoryへ展開して行う。自動で削除・ネットワーク取得・外部公開するscriptは含まない。

## 限界

小例の再現であり、大コーパス、正式性能比較、実復元器のbuildを全て再現するpackageではない。有限テストは全入力証明ではない。Z3検査も同じparserで作った限定modelに対する検査で、公式Wasm意味論からの機械化証明ではない。一般的な普遍量化、等式解析、関係固定点は既知技術である。
