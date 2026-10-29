# 型付きrelay方向の先行研究照合

調査日2026-10-18。検索結果だけ、本文の部分確認、実装実行を区別する。以下の著者実装は今回実行していない。新規性・進歩性の法律判断ではない。

|資料|書誌と一次URL|読んだ範囲・内容|限界と今回の関係|
|---|---|---|---|
|Control Flow Obfuscation for FJ using Continuation Passing|Kenny Zhuo Ming Lu。arXiv:2012.06340、v1 2020、読んだPDFはv2 2021-02-26、13頁Extended Version。[PDF](https://arxiv.org/pdf/2012.06340)。[PEPM2021公式](https://popl21.sigplan.org/details/pepm-2021-papers/6/Control-Flow-Obfuscation-for-Featherweight-Java-using-Continuation-Passing)は *Featherweight Java* 表記、Short-paperとして掲載。|Abstract、§1–2、§5.1–5.2、§6–7、参考文献を確認。seq/loop/ifelse/trycatchの共有により文脈非依存解析で実引数集合が合流する。例では1-call-stringが一部の合流を解く。|FJ例外をCPSへ変換する方式。§7時点では実装中。固定call-stringの限界や一般問題の最悪計算量を、そのまま個々の配布物の解除費用としない。arXiv表紙のConference'17・仮DOIは正式書誌に使わない。|
|Control Flow Obfuscation via CPS Transformation|Kenny Zhuo Ming Lu、PEPM2019、pp.54–60、[DOI](https://doi.org/10.1145/3294032.3294083)。上記2021本文の参考文献12で確認。|出版社への直接取得は失敗。作者掲載PDFの検索抽出ではC向けprototypeとhigher-order combinator/function pointerを確認したが、今回は数値評価を精読していない。|2019の方式を「新しいtyped relay」と呼び替えない。今回の実験は原実装との性能比較ではない。|
|CPS Transformation of Flow Information|Jens Palsberg、Mitchell Wand、JFP13(5):905–923、2003。[著者書誌](https://web.cs.ucla.edu/~palsberg/publications.html)、[著者PDF](https://web.cs.ucla.edu/~palsberg/paper/jfp-to-appear.pdf)。|著者PDFは17頁の出版前版。Abstract、§1–2と§3冒頭を読んだ。定数・条件式付きlambda calculusの特定のCPS変換と0-CFAでは、元の最小flow解からCPS側をannotationサイズに線形時間で構成する。|元と変換後の対応を使う定理であり、未知のWasmバイナリだけの一般解除定理ではない。Luの共有combinatorと同一の変換ともいえない。CPSという名称だけでは解析費用増大を導けない。|
|CPS transformation of flow information, Part II: administrative reductions|Daniel Damian、Olivier Danvy、JFP13(5):925–933、2003、[DOI 10.1017/S0956796803004702](https://doi.org/10.1017/S0956796803004702)。[出版社PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/3DA1271C07DBA366BE4D997C96138FC2/S0956796803004702a.pdf/cps_transformation_of_flow_information_part_ii_administrative_reductions.pdf)。|Abstract、§4、Theorem4.4/Corollary4.5、§5–6を確認。linear beta reductionによる最小解保存とadministrative reduction後のflow情報構成。|非線形な複製まで一律に保存するという主張ではない。今回の要約法の着想と整合するが、Wasmの副作用やtrap保存をこの定理から引用して済ませない。|
|Call graph obfuscation and diversification: an approach|Miguel Rodríguez-Veliz、Yulier Nuñez-Musa、Roberto Sepúlveda-Lima。IET Information Security14(2):241–252、2020。出版社掲載初公開2020-03-01、[DOI 10.1049/iet-ifs.2019.0216](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-ifs.2019.0216)。|書誌、§4.1の導入、§4.4を確認。call edgeをrouter経路へ置換し、独自stackで引数と返り値を運ぶ。|数式が画像である箇所や実験節の精読は未完。性能・耐性の数値を未確認のまま引用しない。呼出しを多段化する一般構成には先行記載がある。|
|Wasm typed function references / tail calls|WebAssembly CGの[function references提案](https://raw.githubusercontent.com/WebAssembly/function-references/main/proposals/function-references/Overview.md)、[tail call提案](https://raw.githubusercontent.com/WebAssembly/tail-call/main/proposals/tail-call/Overview.md)。標準化関連技術資料、査読論文ではない。|導入、呼出し・nonnull referenceの規則、末尾呼出しの設計を確認。typed ref経由でtableを経ずに呼べること、末尾呼出しのframe処理は既知の機能。|提案文書の版に依存する古い型制約を現行仕様全体へ一般化しない。今回使用する構文はWABT/Node/Binaryenで実際にvalidate・実行した。|

今回の論文読解は本文全体の証明監査ではない。PEPMの査読付き発表、arXiv拡張版、JFPの出版前著者版、標準提案資料を区別した。CPS論文の一般複雑度に関する議論から「解析には必ず指数時間が必要」とは推論しない。

## 特許を目指す際の構成対応

[先に確認したUS8645930B2](../patent/signature-and-simd.md)はcommon prototype、function merge等を扱う。各請求項の全要素を無視して「共通signatureは全部権利範囲」と扱うこともしない。

|今回の構成|先行する要素|このゲートの差|
|---|---|---|
|全演算の引数型をi32×2へ統一|common prototype、CPS、function pointer|標準Wasmの型付きrefへ写しただけでは独立した差が弱い|
|同じrelayへ異なる演算refを渡す|共有combinatorの集合合流|heap closureを用いない制限形。共有自体は既知|
|relayを多段化|call routing、固定長call-stringの文脈消失|深さ1/4/8はパラメータ変更|
|return_call/refでframeを再利用|Wasm tail-callの公知設計|通常callとの比較は有用だが、標準機能の効果だけを発明としない|
|引数位置の要約による回復を測る|関数要約・特殊化・beta reduction|評価用の実装。新しい難読化アルゴリズムとは別|

最大のReject理由は、最近接の共有combinator構成に対する独立した技術的差がなく、通常最適化と方式既知の要約が関数間の引数対応を安く解くことである。今回、新たな特許familyや請求項全文の網羅調査を済ませたとは主張しない。
