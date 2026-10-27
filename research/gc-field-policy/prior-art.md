# Oの近接先行技術と読んだ範囲

2026-10-26。新規性を支持する資料だけでなく、主張を弱める資料を優先した。調査で同一実装が見つからないことを、初出の証明にしない。

|資料|書誌・種別|確認した範囲|Oとの重なりと差|
|---|---|---|---|
|[Safe, Untrusted Agents Using Proof-Carrying Code](https://link.springer.com/chapter/10.1007/3-540-68671-1_5)|George C. Necula / Peter Lee、1998、Mobile Agents and Security、LNCS 1419、pp.61–91、DOI 10.1007/3-540-68671-1_5。研究書の章。査読過程は今回確認していない|出版社Abstract・書誌、[著者の説明](https://people.eecs.berkeley.edu/~necula/papers.html)。全文は未取得|事前の安全性証拠検査、data access policy、data abstraction boundaryを扱う。著者ページにはdatabaseへアクセスするuntrusted agentの説明もある。Oの「実行前に安全と判断し、runtime検査を減らす」原理の強い先行。Oは添付された一般証明の検査ではなく限定GC命令・型関係の分析|
|[JVM Specification SE25 §5.4.4](https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html#jvms-5.4.4)|Oracle、Java SE25、仕様文書|field/method/class resolution時のaccess control、protected fieldの継承・receiver制約、private nestの規則|フィールド権限・継承への伝播は既知。Oは構造的GC型・module間canonicalizationを対象にするが、この対象差だけで新原理とはしない|
|[RichWasm](https://michelledaviest.github.io/files/papers/RichWasm-pldi24.pdf)|Michael Fitzgibbons / Zoe Paraskevopoulou / Noble Mushtak / Michelle Thalakottur / Jose Sulaiman Manzur / Amal Ahmed、2024、PACMPL 8 PLDI Article 214、DOI 10.1145/3656444。査読論文|出版版Abstract、Introductionの一部、Limitations、§7・§8の検索箇所。全証明・全実装は未読|細粒度の共有を静的capabilityで保証する先行。rich typed ILを通常Wasmへcompileする。Oは既存Core GC binaryの受理集合制限であり、RichWasmのownership/type safetyを一般に代替しない。arXiv v1だけのプレプリントとは区別し、出版版を主書誌とした|
|[Type Imports and Exports: Private Types](https://github.com/WebAssembly/proposal-type-imports/blob/main/proposals/type-imports/Overview.md)|Wasm提案・非査読|Private Typesとcast/forge問題の本文|秘密型の内容露出・偽造の問題は既知。Oは新しいprivate型をengineへ導入せず、loaderで許可moduleを絞る|
|[GC issue #215](https://github.com/WebAssembly/gc/issues/215)|2021年、仕様議論・非査読|strong encapsulationとcanonical RTTの議論|強いencapsulationの必要性自体は既知|
|[Canonical ABI GC support #525](https://github.com/WebAssembly/component-model/issues/525)|fitzgen、2025-06-03、pre-proposal・非査読|問題設定、immutable/mutable record、rec groupの違い、core-type選択の節|immutable共有、representation変換とcopy費用、rec group同値性の問題が既に具体化。OはWIT値のcopy意味論を実装せず、共有GC objectへの追加権限を検査する。現行Component標準がOを実装済みとはしない|
|[Zero-Copy Cross-Language Object Model #644](https://github.com/WebAssembly/component-model/issues/644)|2026年、設計議論・非査読|四層の区分、typed reference/accessor比較、bulk操作の節|direct accessとaccessor、link-time inline、公開API選択の比較自体も既知。issueの性能予想を実測事実と扱わず、今回既存Binaryen CLIで別途測った|
|[Binaryen #8754](https://github.com/WebAssembly/binaryen/issues/8754)|2026-05-21、issue・非査読|issue本文|外部生成のpublic GC型とclosed-world仮定の整理が必要。ただしOはfuncref全体を制限せず、このoptimizerの全仮定の証明には使えない|

SecWasmのSAS2022書誌・読了範囲は[plan](plan.md)を参照。直接field操作の拒否と一般的な情報流非干渉は別の保証である。

## 現在の差分の強さ

既存engineを変えず、任意producerの**正確なpost-optimization型**へpolicyを結び付け、別moduleのcanonical同値・subtyping・constant expression・array.copyを走査する実装は具体化した。ただし、canonicalizationはwasmparser、アクセス制御は既知、部分共有とcopy回避も既知である。現状の構成が直接一致する既存checkerをこの調査では特定できなかったが、それだけで新しい研究アルゴリズムとは言えない。

主題化には、限定した単一継承・recursive groupを含む健全性定理、自然な既存compiler/pluginでの必要性、既知アクセス制御より意味のある精度・費用・適用範囲の差が必要。現時点は実装と反証の研究記録として保持し、新規性を確立した主テーマとはしない。
