# 可変関数テーブルによる状態移送：反証実験

2026-10-18。採用しない。Wasmの可変funcref tableとbulk table.copyを使う限定変換を実装したが、方式既知の解析で整数状態へ還元できた。新規で有効な方式を確立した結果ではない。継続研究全体は未完了。

## 設計・実装

[先に固定した設計](design.md)、[変換・解除CLI](probe.py)、[独立BigInt参照による検査](check.cjs)。入力は実際の.wasmであるが、任意のWasmに適用できる変換器ではない。privateな固定長funcref table、同型の純粋な整数step関数、規定の反復driverだけを受け付ける。import、memory、global、start、公開tableなどは非対応。ASTの完全一致を使って対象driverを検査し、範囲外は拒否する。

元の状態qをテーブルの循環配置で表し、毎回slot 0を呼び出す。3回のtable.copyで入力依存の回転を行う。しかし不変条件 T[i]=f[(q+i) mod N] により、回転量を累積する整数qだけで同じ呼出しを記述できる。解除器は元バイナリを入力せず、この構造を認識してdriverを置換する。step関数は解析対象のバイナリから保持する。最適化後の認識も限定された既知のAST形状に対応するものであり、一般的な逆コンパイラではない。

## 結果

確定ログは [table-transport-v3](../../results/invention-20261018/table-transport-v3/manifest.json) と [checks.json](../../results/invention-20261018/table-transport-v3/checks.json)。N=4/8/16は一つの人工kernel族のパラメータであり、独立した3アプリではない。

|項目|実測結果|
|---|---|
|比較バイナリ|33本：元・変換・raw解除のraw/O2/O3で27本、最適化済み変換から直接解除した6本|
|正当性検査|各1072入力、計35,376入力条件、不一致0|
|入力|境界値48組、固定seedランダム1024組、同一instanceで連続呼出し|
|適応的解除|変換9条件すべて復元（raw/O2/O3 × N=4/8/16）|
|解除構築時の実行問い合わせ|0。解除後の検証実行は別|
|範囲外・破損規則の拒否|公開table 3件、copy元変更3件、計6件拒否|
|バリデーション|生成・最適化・復元バイナリにWABT validator適用|

O3でのバイト数：

|N|元|変換|raw解除後O3|O3変換から直接解除（再最適化なし）|
|---|---:|---:|---:|---:|
|4|204|253|204|209|
|8|300|353|300|305|
|16|492|553|492|497|

解除時間は各条件1回の診断値で約47–69 ms、WABT入出力等を含む。性能ベンチマークや統計的な攻撃コスト推定には用いない。checks.jsonのinitMillisecondsも単発の初期化診断である。早期の反証が成立したため、実行時間・プロセスメモリの反復性能測定は行っていない。線形memoryを用いないことを「メモリコスト0」とはしない。

全入力の同値性をテストだけで証明したとは主張しない。設計上の局所不変条件と有限の差分検査を区別する。trap、外部副作用、再入、共有tableを含むプログラムへ結果を一般化しない。

## 再現

リポジトリrootから、新しい出力先を指定する。Python 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133を使用。標準ライブラリ以外のPythonパッケージは不要。共通WAT parserとツール呼出しは research/observation-synthesis/transform.py を使用する。ツールは .tools/wabt-1.0.42/bin と .tools/binaryen-version_133/bin に置く（WASM_TOOLS_ROOTで変更可能）。

```powershell
python research/table-transport/probe.py build results/table-transport-reproduction
& 'C:/Program Files/nodejs/node.exe' research/table-transport/check.cjs results/table-transport-reproduction

# 規定driverの実バイナリに対する単独変換・解除
python research/table-transport/probe.py encode results/table-transport-reproduction/4/plain.wasm results/table-transport-reproduction/4/example.wasm
python research/table-transport/probe.py erase results/table-transport-reproduction/4/example.wasm results/table-transport-reproduction/4/example-erased.wasm
```

実験出力先とCLI出力ファイルは未使用の名前にする。manifestに生成物hash、変換・解除時間、認識状態を保存し、checkはhashを確認して実行する。

別ディレクトリで一括再実行し、33本すべてのバイナリhash一致、35,376入力条件で不一致0、解除9/9を再確認した。[再実行監査](../../results/invention-20261018/table-transport-reproduction-v1/reproduction-audit.json) に依存ソース・ツールのSHA-256を保存。[audit.py](audit.py) は2つの実験ディレクトリを引数に比較し、第2ディレクトリへ監査結果を新規保存する。再実行は同じ入力・環境での再現確認であり、独立したベンチマークの追加ではない。

v1は初期の弱いdriver検査、v2は厳密なdriver検査と27本の照合、v3はO2/O3後の直接解除とその6本の照合を追加した履歴である。v2の最適化後「unsupported」は解除器未対応を意味し、耐性の証拠ではなかった。上の結論にはv3のみを使う。

## 次の候補への制約

可変な参照集合や大きいtable自体は保護効果を意味しない。公開された更新操作が低次元の状態に閉じているなら、解析者はその状態だけを追えばよい。回転を一般置換に変えるだけでは既知のdispatcher permutationの延長であり、別原理の候補とは数えない。次の設計では、保護する復元課題を先に固定し、その課題に対する十分統計量・商状態を方式既知の解析者が構成できるかを調べる必要がある。この制約を満たす新方式はまだ定義できていない。
