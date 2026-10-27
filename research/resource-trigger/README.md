# Resource破棄による計算移動の実装・反証

2026-10-19。Component Modelのresource.new/drop、所有権、destructor結線を使う候補を実装した。**独立した発明・主特許候補としては未採用**。生成順の変更はhandle→内部slotの対応を追う解析で除去でき、単純な即時破棄に対する追加解析費用を確認できなかった。全件回復だけを棄却理由にしていない。[先行技術](prior-art.md)、[方式と意味保存条件](algorithm.md)、[結果の分析](analysis.md)、[論文追補](paper-note.md)を参照。

対象は純粋なi32計算鎖で、汎用難読化器ではない。core .wasmを実際に読み、component .wasmへ変換する。出力はJco経由でJS+core Wasmへ展開して実行する。元のcore APIと同じbinary形式ではなく、i32/u32のbit pattern対応を明示した検証である。JSのsigned返り値は`component.run(x >>> 0,y >>> 0) | 0`で得る。

## ファイル

- `prototype.py`：変換、component reader、方式既知の記号解析、回復core生成CLI。
- `run.py`：3族×8/24/64段×4方式×raw/O3の主実験、境界/random、負例、拒否対照。
- `controls.py`：1/3/13/128段、別seed・演算順・payloadの32条件。
- `common.cjs`, `check.cjs`：整数oracle、2独立instance、元/回復coreとの比較。
- `bench.cjs`, `performance.py`：fresh process測定、メモリ、解析費用。
- `verify.py`：独立のPython整数oracleとBinaryen wasm-shellによる元/回復**coreのみ**の検査。
- `replay.py`, `report.py`, `audit.py`：再生成、比較表、整合性監査。
- `plan.md`, `revision-1.md`：事前仮説、Jco表現の反例とbuffer導入理由。
- `dependencies/`：Jcoと依存package-lock。ライブラリ本体は`.tools`内。
- `diagnose-runtime.py`, `runtime-probe.cjs`, `probe.wat`：任意repのbit30が変わるJco経路の最小反例（失敗を再現する診断）。

## 環境

Windows 10.0.26100、Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、WABT 1.0.42、Binaryen native 133、Jco 1.27.0。`jco opt`の内部optimizerはnpm Binaryen **130.0.0**であり、独立core検査のnative 133と区別する。元のcoreツール配置は`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。

Jcoの依存を同じ作業領域に構築する例（ネットワーク取得が必要）。既存研究共通readerとして`research/isotope-swizzle/prototype.py`とその参照先も使用するため、リポジトリ一式で再現する。

```powershell
New-Item -ItemType Directory -Path .tools/component-resource -Force
Copy-Item research/resource-trigger/dependencies/package.json .tools/component-resource/package.json
Copy-Item research/resource-trigger/dependencies/package-lock.json .tools/component-resource/package-lock.json
npm.cmd ci --prefix .tools/component-resource --cache .tools/component-resource/npm-cache --ignore-scripts --no-audit --no-fund
```

## 再現

全スクリプトは既存出力を上書きしない。以下の出力先が既にあれば、新しい名前を指定する。

```powershell
python research/resource-trigger/run.py results/resource-trigger-reproduce
python research/resource-trigger/controls.py results/resource-trigger-controls-reproduce
python research/resource-trigger/performance.py results/resource-trigger-reproduce results/resource-trigger-performance-reproduce
python research/resource-trigger/verify.py results/resource-trigger-reproduce results/resource-trigger-verify-reproduce
python research/resource-trigger/replay.py results/resource-trigger-reproduce results/resource-trigger-byte-replay
python research/resource-trigger/report.py results/resource-trigger-reproduce results/resource-trigger-performance-reproduce results/resource-trigger-report-reproduce
python research/resource-trigger/diagnose-runtime.py results/resource-trigger-runtime-diagnostic
```

単独CLI：

```powershell
python research/resource-trigger/prototype.py transform input.wasm results/demo.component.wasm --mode deferred --seed 37
python research/resource-trigger/prototype.py transpile results/demo.component.wasm results/demo-js
python research/resource-trigger/prototype.py recover results/demo.component.wasm results/demo.recovered.wasm
```

## 実測の保存先

主[manifest](../../results/invention-20261019/resource-trigger-v3/manifest.json)と[正当性](../../results/invention-20261019/resource-trigger-v3/check.json)、追加[正当性](../../results/invention-20261019/resource-trigger-controls-v1/check.json)、[最終性能](../../results/invention-20261019/resource-trigger-performance-v2/summary.json)、[比較表](../../results/invention-20261019/resource-trigger-report-v3/comparison.md)、[core別実行器](../../results/invention-20261019/resource-trigger-verify-v1/summary.json)、[byte再現](../../results/invention-20261019/resource-trigger-replay-v1/summary.json)、[監査](../../results/invention-20261019/resource-trigger-audit-v2/summary.json)。

失敗も保存：v1はO3後のoperand stackのreader不備、v2はrepのbit30を失うJco実行経路の正当性失敗。[小さい反例](../../results/invention-20261019/resource-trigger-runtime-probe-v1/probe.json)にも同じ挙動を保存。report-v1は集計器のgenerator消費ミス。performance-v1は短い測定区間のばらつきが大きいため、実行測定をv2で置き換えた。解析器は変更しておらず、360回の解析記録はSHAを照合してv2へ引き継いだ。これらを解析耐性や実行成功に数えない。
