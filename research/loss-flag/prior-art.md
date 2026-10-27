# 先行資料との照合

2026-10-22。新たな本体アルゴリズムの独立性は確立していない。既存prefix-repairの保存戦略の拡張として扱う。

| 一次資料 | 区分・読んだ範囲 | 関連と限界 |
|---|---|---|
| Daniele Cono D’Elia, Camil Demetrescu, **On-Stack Replacement, Distilled**, PLDI 2018, DOI 10.1145/3192366.3192396、[著者PDF](https://season-lab.github.io/papers/osr-distilled-pldi18.pdf) | 査読会議。Abstract、Introduction、§5.2末尾のlive/avail、§5.3を今回確認 | 現状態から値を再構成し、再構成できない値だけ生存させる考えと、memory補償が先行する。今回のcopy-loss flag生成と同一だとは確認していない。著者のLLVM実装との性能比較はしていない。 |
| Cong Hou, George Vulov, Daniel Quinlan, David Jefferson, Richard Fujimoto, Richard Vuduc, **A New Method for Program Inversion**, CC 2012, LNCS 7210, pp.81–100, DOI 10.1007/978-3-642-28652-0_5、[出版社](https://link.springer.com/chapter/10.1007/978-3-642-28652-0_5) | 査読会議。出版社の書誌・Abstractを確認。著者URLの試行は取得不可、CiteSeer本文openは403。検索抽出の本文断片を全読の代用にしない | 値の回復可能関係をgraphにして逆プログラムを生成する既存の構成。現状態からの再構成一般を新規とは言えない。本文の算法詳細や本案との厳密包含、著者性能値の再現は未確認。 |
| Cristian Cadar, Periklis Akritidis, Manuel Costa, Jean-Philippe Martin, Miguel Castro, **Data Randomization**, MSR-TR-2008-120, 2008年9月、[技術報告](https://www.microsoft.com/en-us/research/wp-content/uploads/2008/09/tr-2008-120.pdf) | 読んだ版は技術報告。Abstract、Introduction、§3.1の等価クラス・union-findを今回確認 | プログラムのalias制約から表現を割り当てることが既知。複数byteのblock三角表現と同一ではないが、操作に合わせてcodecを選ぶ一般発想は先行。メモリ破壊防御という別の攻撃モデルの効果をIP保護へ流用しない。 |
| **WebAssembly Core 3.0, memory.copy**、[実行仕様](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy) | 取得表示2026-10-20。range checks、重複copyの順序を確認 | 書込み前の範囲検査という意味を利用してtrap直前修復を出力する。仕様利用自体が発明ではなく、同種の意味を持つ他形式にも適用可能。 |

リポジトリ内では、copy-centralizer/copy-fiberは各copyとの可換性、prefix-repairは入口保存値、wait-partitionは観測射影との整合性を使う。本案は情報損失に合わせた表現選択で現memoryによる修復を可能にする。ただしkernel保存・写像の因子化・block三角行列自体は標準的な数学であり、wait-partitionの射影適合とも原理的に近い。原理の異なる第4案などと水増ししない。

具体的差分候補は「Wasmの全trap prefixが失う情報を解析し、入口履歴なしで修復できるBと出口コードを一緒に生成する」点。得られた速度差は同じBの共有入口保存を対照としたもので、既存研究一般を上回った結果ではない。

検索語：`compiler data representation kernel copy obfuscation`、`checkpoint side information linear program`、`obfuscation information loss encoding`、`reverse computation reconstruct state saving compiler`、`obfuscation kernel linear maps`、`A New Method for Program Inversion Hou Vulov Vuduc 2012 pdf`。前半の検索は画像・個人情報秘匿等の別分野が多く、本案の先行性の根拠にはしなかった。関連特許の請求項・ファミリーを網羅調査したとはしない。

最大のReject理由は、既知の再構成可能性と線形表現選択の具体化を超える独立性を示せず、さらに同じ公開decoderから同じ回復器で戻せること。工学的部品として保持するが、主発明には採用しない。
