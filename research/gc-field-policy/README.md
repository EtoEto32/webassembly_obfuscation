# O: GCフィールド権限の受理時検査

現在は限定した研究仮説。Wasmの構造的GC型について、参照を直接共有しながら第三者moduleのread/write/createを受理時に制限する。実行時の書換えや検査命令は加えない。**これだけで新規性が十分、または一般的な情報流保護が成立したとは判定していない。** [設計と事前計画](plan.md)、[実測と限界](results.md)。

## 再現

既存workspaceのRust、Python 3.9、Node 24.15.0、Wasmtime Python 50.0.1を利用する。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/gc-field-policy/checker/Cargo.toml --release --offline --locked --target-dir .tools/gc-field-policy-target
python research/gc-field-policy/experiment.py results/gc-field-policy/fresh-probe
python research/gc-field-policy/boundary.py results/gc-field-policy/fresh-boundary
python research/gc-field-policy/workload.py results/gc-field-policy/fresh-workload
python research/gc-field-policy/workload-contract.py results/gc-field-policy/fresh-contract
python research/gc-field-policy/link-comparison.py results/gc-field-policy/fresh-workload results/gc-field-policy/fresh-link
python research/gc-field-policy/audit.py results/gc-field-policy/fresh-audit.json
```

別環境で初回依存取得する場合は`--offline`を省略する。Python packageは`.tools/import-alias-quotient-python`から読み込む。Rust依存はCargo.lock。WAT assemblyはWasmtime packageの`wat2wasm`で行い、wasmparser 0.227.1とNode/Wasmtimeで検証・実行する。

CLI:

```powershell
.tools/gc-field-policy-target/release/gc-field-policy.exe LIBRARY.wasm POLICY.json CONSUMER.wasm
```

policyは信頼するlibraryの型index、`read`/`write`/`create`、field indexを指定するJSON配列。例は実験結果の`policy.json`。module間の比較はwasmparserの同一canonical type contextで行い、名前やindexの一致だけに頼らない。CLIの5 modeは検査なし・不完全対照・closure・全aggregate操作拒否の比較結果を返す。

`loader.mjs`の`admit`は、コピーした実binaryとpolicyをstdin経由でcheckerへ渡し、closureに合格した同じbyte列だけをNodeでinstantiateする。ファイルを再読した別versionへ判定を使い回さない。これは検証用の同期loaderであり、stdin JSON配列の転送費用・外部process起動費用がある。完成した汎用plugin製品ではない。

`admit`の第5引数は任意のimport名許可リスト（module名はlibに固定）。省略時はlibの全exportをリンク候補にするため、trusted API契約の確認が別途必要。workloadはinit/private-atをconsumerに渡さない明示allowlistを使う。GC checker自体がAPIの意味を検証したとは扱わない。

最新の360process比較では、既知のデータ分離・増分public viewに対する明確な実行優位はなかった。[近接先行技術](prior-art.md)を含め、新しい主アルゴリズムとしての採用は見送る。実装と反証結果は保持する。

auditは保存済み8manifestの326ファイルのhashと、最新生成器による10binaryのbyte再現を確認する。全研究directoryの監査や全入力同値性証明ではない。link-v3の主測定前にあった2件のdriver/feature失敗もresults内へ残した。

[日本語研究ノート](research-note.md)に構成・実測・採否をまとめた。[次方向の反証](next-direction-screen.md)にはcustom descriptor、exception tag、GC canonical ABIの検討を記す。descriptorの真正性仮説はBinaryen interpreterの4条件で反証され、Nodeはencoding未対応だった。新しい主案を実証したとは数えない。

## 保証の境界

全untrusted Core Wasm moduleをloaderで検査し、host/imported APIが信頼されるという前提。指定型の全instanceに一様な権限を適用し、同じcanonical型を使う別libraryのobjectを識別しない。保護するのは直接のaggregate read/write/create。array length、type test、identity、timing、資源消費、許可APIが返す情報は別扱い。

allowed featureはCore 2相当＋GC・typed function references・tail calls・extended const。その他のproposalは拒否する。const expression中のconstructorも走査する。動的flowを見ないので安全なコードを拒否し得る。数学的健全性や任意moduleの完全性はまだ証明していない。
