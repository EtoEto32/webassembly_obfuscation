# 今回の先行技術と読了範囲

調査日2026-10-19。実行したのはローカルの限定プロトタイプであり、以下の作者実装を追試したという記録ではない。

|資料|種別・確認範囲|今回との関係と限界|
|---|---|---|
|Will's Root, *corCTF 2023 vmquack's vectorized vices: VM Obfuscation through AVX-512*, 2023-08-02。[作者記事](https://www.willsroot.io/2023/08/vmquack-avx512.html)|公開技術記事、査読論文ではない。register/index pair、mask、演算移送、devirtualizationの記述を読んだ。記事はanematodeとの共同challenge制作に言及。|SIMDのレーンへVM値を置く保護は既に公開され、作者自身が命令列からscalar操作へ戻す方法を述べる。本案はWasmの4lane仮入力と入力依存frameだが、SIMDへ載せる発想自体は新規でない。|
|Cameron Babcock, *The Shape of an Operation Is a Signature: Inside ObfTypes*, 2026-05-03、更新2026-07-01。[作者記事](https://cameronbabcock.net/blog/obftypes-compile-time-polymorphism/)|公開技術記事。直接openはエラー。ドメイン指定の検索抽出で本文のSIMD Variants・Proof Scope・Limitsを確認。|scalar操作をvector laneへ移して取り出す同値変形を述べる。測定や実装全体のcoverageを記事は提供していない。今回の動的frame方式と同一という断定はしない。|
|LLVM project, *InstCombineSimplifyDemanded.cpp*。[公式ソース表示](https://llvm.org/doxygen/InstCombineSimplifyDemanded_8cpp_source.html)|公開実装。表示版24.0.0git。SimplifyDemandedVectorEltsのコメント・複数利用者処理・逆伝播の一部を確認。全実装監査ではない。2019の[D67345](https://reviews.llvm.org/D67345)は検索抽出のみ、直接open失敗。|必要な要素からvector計算を簡略化する原理は既知。本解析のsymbolic mod4 cursorをLLVMがそのまま実装しているとは述べない。LLVM本体を今回のWasmへ実行して比較した結果でもない。|
|WebAssembly CG, *128-bit packed SIMD Extension*。[公式提案](https://github.com/WebAssembly/simd/blob/main/proposals/simd/SIMD.md)|標準化技術資料。lane、splat/extract、shuffle/swizzle、wrapping arithmetic節を確認。repositoryはarchive済みで、現行全仕様をこの一資料だけで代表させない。|4byte境界を保つ移送と範囲外swizzleのzero化を意味保存・負の対照へ使用。今回の構文はWABTとNodeでも実際にvalidateした。|

独立した技術差の候補は、固定のVM register/indexではなく、節点ごとの入力依存frameと複数の仮入力を保ちながら演算を行う規則である。しかし生成時のframe整合性が逆向き解析でもそのまま使え、1レーン需要へ縮む。このため、差分が追加の解析負担をどれだけ生むかは実測で限定して扱う。既存記事に完全一致の例が見つからないことを新規性・進歩性の証拠にしない。今回、新たな公開特許の請求項全文調査は完了していない。

## 他に検討して選ばなかった方向

1. **GC型・参照フロー**：既存の[型同一性検査](../../tmp/candidate-screening/README.md)、[GC alias gate](../alias-circuit/README.md)と比較。型名やrecursive groupの変更だけでは静的識別を避けない。型付きCPSは[共有relayの先行記録](../typed-relay/prior-art.md)と重なる。新しい生成規則を確立できず今回の実装対象にしなかった。
2. **非可換置換列**：Alexander Koch / Stefan Walzer, *Private Function Evaluation with Cards*, New Generation Computing **40:115–147 (2022)**、公開2022-02-12, [DOI 10.1007/s00354-021-00149-9](https://link.springer.com/article/10.1007/s00354-021-00149-9)。査読誌論文。書誌、要旨、Barrington構成・群作用に関する節を確認した。DOI中の021を発表年と取り違えない。Boolean計算を幅5の置換列へ移す原理は既知であり、SIMD実装だけを新方式と数えない。カードの非公開shuffleを使うモデルの安全性を、公開の置換だけのWasmへ移して主張することもしない。
3. **時間方向の計算移送**：Jean-Baptiste Tristan / Xavier Leroy, *A Simple, Verified Validator for Software Pipelining*, POPL2010, pp.83–92。[著者書誌・要旨](https://xavierleroy.org/bibrefs/Tristan-Leroy-softpipe.html)を確認。本文の全証明は未読。loopの時刻をずらすだけでは既存のsoftware pipeliningと区別できる生成規則がないため保留。

これらは探索で棄却・保留した方向であり、独創的なアルゴリズム3件を完成したという数え方はしない。今回のSIMD仮説も、新規かつ有効な主発明と認定したものではない。
