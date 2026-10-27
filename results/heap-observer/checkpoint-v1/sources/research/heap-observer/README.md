# Wasm GCの外部読出しモジュール

2026-10-27。**対象programとengineを改変せず、外へ渡されたGC objectの内容・循環・共有を、生成した別Wasm moduleから観測できた。新しい検出アルゴリズムや修士主テーマの十分な新規性は、まだ確立していない。** [実装前計画](plan.md)、[実測](results.md)、[先行性と次の判断](prior-art.md)。

実装はbinaryのtype sectionを読み、rec groupの境界・順番・supertype・finalityを保ったままhelperへ複製する。型ごとのref.test、struct.get、array.len/getを追加し、JS側から公開済参照を渡す。BFSと既知の参照番号付けで、最大node数とarray要素数を制限したsnapshotを作る。対象のcode sectionを変えないためtarget増分は0 byteだが、別helperとhost処理の費用は発生する。

比較には**元binaryから作った同じhelper**を用いる。最適化後の型番号から別helperを作って番号を直接比較してはいない。open-worldとclosed-worldを区別し、外部検査が許可されていないclosed-world最適化に対するfield差は不具合判定から除外する。この契約の区別自体はBinaryenの既存仕様である。

## 再現

Windows / Python3.9 / Rust1.97 nightly / Node24.15.0 / SpiderMonkey150.0.1 / Binaryen133 / Wasmtime Python50.0.1。Rust dependencyはwasmparser・wasm-encoder0.262.0、serde_json1.0.142、Cargo.lockあり。PythonのWasmtimeは既存 `.tools/import-alias-quotient-python` を参照する。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/heap-observer/tool/Cargo.toml --release --locked --offline --target-dir .tools/heap-observer-target
python research/heap-observer/experiment.py results/heap-observer/fresh-probe
python research/heap-observer/generated.py results/heap-observer/fresh-generated
python research/heap-observer/bounds.py results/heap-observer/fresh-bounds
python research/heap-observer/benchmark.py results/heap-observer/fresh-performance
python research/heap-observer/audit.py results/heap-observer/fresh-audit
```

出力先は新規directory。`generated.py` は前段の `results/boundary-alias/caller-v1` に保存された128 binary・metadataとBinaryenのupstream harnessを使う。`audit.py` は保存済みprobe-v2/generated-v1を監査する。全工程を新規環境で一括再実行したという意味ではない。

helper単体CLI：`.tools/heap-observer-target/release/heap-observer-tool.exe INPUT.wasm OUTPUT.observer.wasm`。成功時のstdout JSONをmetadataとして保存する。入力は1 MiB以下のvalid core module。未対応型等はJSONのrejectedで返し、helperを書かない。callerはexit statusだけでなくJSON statusを確認する必要がある。

## 範囲と限界

struct/array、packed field、i32/i64/f32/f64、参照field、recursive type、single inheritanceに対応。非公開のrootを取得する機能はない。shared type、custom descriptor、continuation、例外参照、v128 fieldは現試作で拒否。任意のJS object・function内部はopaqueのまま。生成物に使われない未対応型があっても全moduleを拒否する保守的実装である。

snapshot番号は各境界eventでリセットする。event間のidentityは既存boundary oracleを併用する。node/element上限に達したときはtruncationを記録する。NaN payloadは正規化するため、その違いを検出するoracleではない。Mapへの参照保持や追加呼出しがGC時期・JIT挙動・時間へ与える影響は排除していない。今回のguest呼出しstatusが一致したことは、任意programの非干渉証明ではない。
