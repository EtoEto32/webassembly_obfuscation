# wasm-smith追加試験の再現

既存Rと同じWindows/Python/Wasmtime環境に加え、Rustと公式wasm-smith 0.262.0を使う。Cargo.lockはsmith-driverとsmith-pristineに保存。無改変crateと変更copyを分離している。既存の結果directoryを上書きしない。

初回だけrepo rootで:

```powershell
python research/gc-witness/fetch-smith.py .tools/gc-witness-smith-upstream
python research/gc-witness/prepare-smith.py
```

fetchは公式crateだけを取得し、サイズ・archive pathを検査する。既存の取得済み環境ではこの2行を繰り返さない。prepareは変更済みcopyを上書きしない。ネットワークなしでは取得済み依存が必要。

以後は新しい出力先へ:

```powershell
python research/gc-witness/smith-reproduce.py results/gc-witness/smith-fresh --offline
```

依存cacheがない新環境では`--offline`を外す。scriptはstock/zero/pristineとcheckerを順にbuildし、mask校正、512生成試行、256 baseline照合、2,022入力呼出しと45校正、全出力再生成監査を実行する。source取得・buildを除く各構成scriptは実際に完走済み。一括wrapperの追加完走は未実施。

既存保存物を再集計・再生成する場合:

```powershell
python research/gc-witness/smith-audit.py results/gc-witness/smith-v2 results/gc-witness/smith-input-v1 results/gc-witness/smith-fresh-audit
python research/gc-witness/audit.py results/gc-witness/fresh-full-audit
```

結果sourceのexeは当時のbuildを再実行するためのローカル保存物。第三者は内容を確認してsourceからbuildできる。CPU時間やファイルの絶対pathは環境間で同じになるとは限らない。生成byte/分類の再現と速度測定の再現は区別する。
