# 外部Wasm解析器の基準確認

[実測と再現方法](../../results/invention-20261023/disrobe-report-v1/report.md)。Disrobe v0.10.6を公式checksum確認後に27入力へ適用した。新発明の件数には加えない。

- 未変換リスト9本：C/JSON/WAT生成は正常終了。生成WATはvalidationを通るが初期dataが欠落し、5,148呼出し中504が不一致。正解dataを戻す診断は全件一致。
- 整数式18本：生成WATの75,906呼出しで不一致0。別deob処理の18出力は入力とbyte一致し、既存の適応射影による回復を否定しない。
- Cは固定offsetのi32 loadと局所変数へ戻るが、リストのnext pointer型・record strideの回復は確認できない。Cの再コンパイルは未実施。

この測定により『出力ファイルがある』『Wasm validationに通る』『正しく実行する』『構造を回復する』を別の項目として管理する。NotDecの代替実測とは扱わない。
