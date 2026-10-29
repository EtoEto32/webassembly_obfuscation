# 失敗したWasm初期化から残った関数参照の失効実験

[結果と厳格な判定](results.md)。動作するbinary rewriterと2engine実験はあるが、新規アルゴリズムとして主テーマに採用する根拠は未確立。既知のguardによる強い対照を含む。

## 再現

Windows、Rust、Python 3.9、Node 24.15.0、WABT 1.0.42、Wasmtime Python 50.0.1。依存の配置は既存workspaceの`.tools`を利用する。Rust依存はCargo.lockで固定。第三者環境ではWABTとWasmtime Pythonの配置に合わせ`experiment.py`等の定数を変更する必要がある。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/failure-revocation/rewriter/Cargo.toml --release --offline --locked --target-dir .tools/failure-revocation-target
python research/failure-revocation/experiment.py results/failure-revocation/fresh-probe
python research/failure-revocation/performance.py results/failure-revocation/fresh-performance
```

出力先は新しいディレクトリを指定する。`--offline`はこのworkspaceのcache向け。初回取得する別環境では省略する。Rust依存はwasmparser/wasm-encoder 0.227.1、serde_json 1.0.142。

```powershell
.tools/failure-revocation-target/release/failure-revocation.exe refs INPUT.wasm OUTPUT.wasm
```

modeは`entry`（全定義関数）、`address`（参照可能な元関数のみ）、`refs`（参照を一意なwrapperへ置換）。出力は`__failure_gate.alive`というhost所有のmutable i32 globalを要求する。1で開始し、同期instantiationの例外を捕捉したら他へ制御を返す前に0へする。成功なら1のまま。gateはinstance間で使い回さず、guestへ別経路で渡さない。完成したセキュリティ製品ではない。

試験sourceと生成binary、command、環境情報、hash、全観測、性能の生データは各結果directoryに保存する。Python bindingから受け取るcallbackのfuncrefを保持するときだけ、ctypes値をcopyするadapterを試験側に置く。インストール済みpackageは変更しない。
