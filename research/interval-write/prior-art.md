# 区間上書き案の先行技術確認

2026-10-18。読んだ範囲を限定して記録する。今回の早期試作の新規性・特許性を認定するものではない。

|資料|種別・書誌|実際に読んだ範囲／含意|
|---|---|---|
|[The M/o/Vfuscator](https://recon.cx/2015/slides/recon2015-14-christopher-domas-The-movfuscator.pdf)|Christopher Domas、REcon 2015発表スライド。査読論文とは区別。|表紙とPDF pp.17–19、45–49を含む比較の説明。scratchへの2回の書込みとreadで等値判定し、256byteの領域を用いる構成を確認。メモリの別名関係で比較する一般発想は先行する。今回の区間fillによる大小比較と完全に同一とはしていない。|
|[M/o/Vfuscator repository](https://github.com/xoreaxeaxeax/movfuscator)|Chris Domas、公開実装・README、2026-10-18閲覧。|Overview、Recommendations、Limitations。算術・比較等をmovへ変え、lookupを使う説明を確認。著者ツールは今回実行していない。今回のtable対照は自作のWasm実装である。|
|[Demovfuscator repository](https://github.com/leetonidas/demovfuscator)|Julian Kirsch、Clemens Jonischkeit、公開実装・README、2026-10-18閲覧。関連発表はREcon 2016。|SummaryとUsage。静的taintとSMTを組み合わせ、不変条件に基づく回復を説明。著者によるCTF例への適用報告はあるが、今回の実行・定量比較ではない。コード全体と学位論文は未読。今回の回復器をDemovfuscatorの再実装と呼ばない。|
|[Bulk Memory Operations and Conditional Segment Initialization](https://raw.githubusercontent.com/WebAssembly/bulk-memory-operations/master/proposals/bulk-memory-operations/Overview.md)|WebAssembly project、仕様提案文書。査読論文ではない。|Designとmemory.fill節。宛先・byte値・長さによるfill、境界検査の説明を確認。multi-memory以前の説明が残る歴史的文書であり、現在の単一memory制約とは解釈しない。|
|[Multiple Memories for Wasm](https://raw.githubusercontent.com/WebAssembly/multi-memory/main/proposals/multi-memory/Overview.md)|WebAssembly project、仕様提案文書。|Summary/Motivation/Instructions。公開memoryと私有memoryの分離を動機として明記し、memory indexを追加する。非export memoryの使用自体は新規ではない。|

## 構成差と実測による判断

今回の具体的な生成規則は、`a<b` を「256byte初期化、先頭b byteの上書き、位置aのload」へ変え、同じbを使う比較間で構築を共有する。Domasの等値判定と、個々の比較全体を二次元表にする方式とは実行手順が異なる。ただしこれは順序関係の表の省メモリ構築としても説明でき、単に使う命令がWasm bulk memoryになったことを独立した新規性にはしない。

[実験](README.md)では個別版から共有版への費用削減があった。一方、上書き領域を読む解析から元の比較が安く取り出せる。したがって新規で有効な主方式としての根拠は不足する。新しい数学原理を要求しているのではなく、具体的差分が保護上の改善へ結びつくかを判断している。

追加検索語は `obfuscation memset comparison`, `obfuscation memory copy algorithm`, `memory.fill comparison WebAssembly`, `obfuscation memory equality alias` 等。公開特許の検索ではUS20070234070A1（pointer equalityを使うopaque predicateの断片）等が出たが、今回その請求項全文は読んでいない。これらを構成照合済みとせず、先行技術不存在・特許性・FTOの結論は出さない。外部公開・push・出願は行っていない。
