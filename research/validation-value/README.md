# Wasm型検査の妥当性による条件計算

2026-10-22。共有memoryの表現変更とは別の実験として、CNF条件式を入力依存の検証用Wasmへ変換し、標準validatorの真偽を返す方式を実装した。**動作は確認したが、独立した新規性と保護優位は未確立で、主発明には採用しない。** 有限環方式の構成的候補とは別の負の結果である。

[計画](plan.md)、[規則・意味保存・攻撃モデル](algorithm.md)、[先行資料](prior-art.md)、[草稿追補](paper-note.md)。公開されたdecoderを持たなくても、呼び出す検証器の意味を要約すれば通常のBoolean式へ戻ることを確認した。

## 結果

主結果：[validation-value-v3](../../results/invention-20261022/validation-value-v3/manifest.json)、[監査](../../results/invention-20261022/validation-value-audit-v1/audit.json)。同じCNF族の3つの生成条件（16/32/64変数、8/20/48clause）であり、実アプリ3件ではない。uniqueなcore artifactは18本。validatorと専用recognizerは同じ生成器binaryに異なるホストadapterを使うため、実行条件は24になる。

- 元版／生成器＋validator／生成器＋recognizer／回復版、raw/O3の24条件で53,456呼出し一致（真16,192、偽37,264）。境界、walking bit、clauseを偽にする入力、既知の真入力、固定seed乱数を含む。
- 補助byte列の縮小例93件はNodeとWABT validatorの両方で一致。67件がvalid、26件が意図したinvalid。invalidを解析器未対応や外側programの失敗と数えない。
- 生成器の全6条件から、入力oracleを一回も呼ばず通常のCNFを回復。6つの回復scalar式は、元式との全64bit入力の不一致がZ3でunsat。生成器全体や任意hostの形式証明とは区別する。
- 18binaryをbyte一致で再生成。元・回復のpure binaryはWABT interpreterで72呼出し一致。外側validator版をWABT interpreterで実行したとはしない（JSホスト契約を要する）。
- 3非対応入力と1破損templateを拒否。回復を各条件7回、計42回繰り返した。WABT読出し・再コンパイル・validation込みの中央値はraw約38.5～50.1ms、O3約37.9～44.2ms。実行queryは0。

## 実行費用

O3入力の中央値。各条件3個のfresh Node process、1,024回warmup、7batch、batch目安15ms。合計36process/252batch、10ms未満のbatchなし。JSからの呼出しと入力生成、ホストcallbackを含む。CPU affinityや周波数は制御していない。

| 条件 | 元 ns/call | validator | 専用recognizer | 回復版 | validator/元 |
|---|---:|---:|---:|---:|---:|
| access | 19.816 | 2,699.133 | 226.393 | 20.279 | 136.21 |
| compat | 26.491 | 3,155.957 | 566.342 | 26.964 | 119.13 |
| features | 44.221 | 3,905.908 | 1,480.292 | 46.796 | 88.33 |

専用recognizerは生成器の到達template族だけを処理する対照で、汎用Wasm validatorではない。回復版のO3という名前はO3入力から回復した意味で、回復後の再最適化は行っていない。回復版は元の約1.018～1.058倍の時間に戻る。通常最適化がhostの意味を知らずに残す処理を、保護効果とは数えない。

O3サイズ：元203/532/1,344bytes、validator版446/1,173/3,097bytes、回復版287/873/2,517bytes。検証用byte列88/206/506bytes。元・回復のlinear memoryは0、生成器は固定64KiB。whole Node maxRSSは42,696～44,396KiB。変換時間は約41.0/42.6/51.1ms（各1測定、WABT込み）。host adapterのソースサイズはcore binary表へ含めていない。

## 再現

Windows 10.0.26100、Python3.9、Node24.15.0/V8 13.6、Intel Core i9-11900K、WABT1.0.42、Binaryen133。本体はPython標準ライブラリだけを使う。監査はZ3 Python bindingを使い、リポジトリの `.tools/encoding-synthesis-python` または通常のPython環境からimportする。使用版はaudit.jsonに保存。

```powershell
python -X utf8 research/validation-value/run.py results/validation-new
python -X utf8 research/validation-value/audit.py results/validation-new results/validation-audit-new
python -X utf8 research/validation-value/report.py results/validation-new results/validation-audit-new results/validation-report-new
python -X utf8 research/validation-value/prototype.py transform source.wasm protected.wasm
python -X utf8 research/validation-value/prototype.py recover protected.wasm recovered.wasm
```

出力先は未作成の名前にする。主記録のv1はO3の零byte省略、v2は`x >>> 31`の0/1性を回復器が認識できず停止した。v3で解析器を修正し、全条件を回復した。v1/v2のunsupportedを耐性や成功件数へ加算しない。失敗ログを保持している。

元の純粋関数へhost importとmemory exportを追加する契約変更があり、任意のWasm hostへの透明な差替えではない。外部公開・push・出願は行っていない。設計・実装・実験は成果として保存するが、特許の柱となる有用な新規難読化を確立したとは報告しない。
