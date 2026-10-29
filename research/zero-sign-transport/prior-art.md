# 先行技術と今回読んだ範囲

2026-10-21。全文未読の資料や検索不発を、新規性の証明に使わない。今回の案は暗号方式ではなく、秘密鍵を仮定しない公開プログラム変換。

## FLOBの版差

Yikun Hu, Zichen Zhao, Peixiang Qin, Ziyi Zhou, Jiaping Gui, Yuandao Cai, Wensheng Tang, **Protecting Floating-Point Computation for DNN Binaries with MBA Obfuscation**, 2026, arXiv:2607.17603。[書誌](https://arxiv.org/abs/2607.17603)。査読済み発表先は今回確認しておらずプレプリントとして扱う。

[v1 HTML](https://arxiv.org/html/2607.17603v1)のAbstract、§2–3、§6.3を読んだ。高精度表現へ持ち上げてMBAを適用する設計を確認。[v3 HTML](https://arxiv.org/html/2607.17603v3)の§1、§3–6も読んだ。v1の実装・評価済みの記載から、v3では実装・評価を予定とする記載へ変わっている。理由は未確認。初版の性能値・回復率を確立した実測として引用せず、我々の速度と比較しない。

今回の案はnative f32の丸めを各演算に残し、零符号を別に伝える。高精度整数MBAとは手順が異なる。ただし、これで未知の同一先行手順まで排除したとはしない。

## 仕様と通常の最適化

- WebAssembly Community Group, [Numerics, Core 3.0](https://webassembly.github.io/spec/core/exec/numerics.html)、取得時表示2026-10-20。fadd/fsub/fmulとNaNの記載を確認。反対符号の同じ大きさの加算は+0、同符号の零加算はその零、乗算の零符号は符号の積となる。仕様に従う符号操作自体は新技術ではない。
- [LLVM Language Reference](https://llvm.org/docs/LangRef.html)、nszとmin/max・copysignの節の検索結果を確認。零符号を無視する条件の指定と符号伝播は既存のコンパイラ概念。今回nszを仮定せず出力bitを保存するが、保護効果とは別の正当性条件である。
- [Wasm design rationale](https://github.com/WebAssembly/design/blob/main/Rationale.md)、NaN bit-pattern nondeterminismとNaN-boxingの節を確認。payloadの固定的伝播を利用する案は採らない。

## 公開特許との構成比較

**EP4339835A1, Machine learning model protection**。Robert Durand, Philip Eisen, Thomas Hickie、公開2024-03-20。[公報](https://patents.google.com/patent/EP4339835A1/en)の書誌と請求項1–15を確認。モデルから生成するソフトウェアへの保護、従属項の固定小数点・精度指定・node関数化が関連する。今回の零符号を遅延伝播する規則との同一性は確認していない。明細書全体、審査経過、登録後の請求項は未調査。権利範囲・有効性・非侵害・特許可能性を判断しない。

一般的な符号化領域での計算と公開復号については[既存の関係式調査](../patent/joint-relations.md)も近い。既知の表現変更にIEEEの例外修復を添えただけ、という査読の反論が最も強い。今回の評価では遅延修復の費用とphase正規化による回復を両方検査し、正しいだけで新発明としない。

## 公開実装とさらに近い既知の操作

- **Obfuscator-LLVM, Instructions Substitution**、公式wiki、表示最終編集2017-06-29、非査読の実装資料。[該当節](https://github.com/obfuscator-llvm/obfuscator/wiki/Instructions-Substitution)のDescriptionと加減算例を読んだ。符号反転を使う整数式の置換を既に提示し、浮動小数点への適用は丸め誤差を理由に対象外としている。符号の移動や見かけ上の加減算変更を本案の新規性とはしない。
- **codesome/Obfuscation-LLVM**、公開コードの[README](https://github.com/codesome/Obfuscation-LLVM)、年・正式リリース未確認、非査読。`-obfus-float`はadd/mul/subの難読化と精度低下の可能性を記す。公式Obfuscator-LLVMとは別リポジトリ。ArithmeticObfuscationのソース取得はweb cache miss・API取得不可・terminalのDNS失敗で完了せず、具体的な置換規則を読んだとは扱わない。ビルドも性能比較も未実施。本案と同じ遅延修復を持たないと断定できない。
- **GCC 14.2, Optimize Options**、公式実装資料。[該当節](https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Optimize-Options.html)の`-fno-signed-zeros`、`-fassociative-math`、`-funsafe-math-optimizations`を読んだ。零符号を無視すると許される変形が増えることは既知である。今回は零符号を出力で保存するが、それ自体を新しい保護原理とは主張しない。
- **max.xz.ax, corCTF 2025 whatever-floats-your-boat**、2025年のCTF作者の[技術解説](https://max.xz.ax/blog/boat-vm-x86-floating-point-exceptions/)、非査読。The Virtual MachineとAbout Floating Pointsを読んだ。x86の蓄積するFP例外状態を分岐に使う独自VMであり、本案の零符号の別計算とは異なる。浮動小数点の特殊な挙動を難読化に使う広い着想は既出である。Wasmで同じ例外flagを読めるとは仮定しない。

追加検索は2026-10-21に `"obfuscation" "signed zero" floating point` と `"floating point" obfuscation "sign" encoding deferred` を使用した。検索結果に現れただけの資料を読了文献に加えていない。これらの照合で支持できる差は「丸めを各nodeに残した符号表現と、出力が零の時に限る論理符号の再構成」という具体手順に限る。同一手順の先行公開の有無は未確定。
