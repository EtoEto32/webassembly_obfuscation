# Wasm GCの参照共有によるBoolean回路：設計・実装・反証

2026-10-18。**有効な新規難読化としては不採用。** 前の整数・table・対称式の試作とは異なり、今回はGCオブジェクトの同一性と破壊的更新で演算を実行した。しかし共有関係を15通りに分類する解析で、最適化後もGCを使わない回路へ戻せた。参照共有による難読化自体は先行しており、独立した新発明として数えない。

## 仮説と規則

仮説は「各gateで新しい参照を作り、数値に変換できない参照の同一性にBoolean値を載せれば、有限の具体値を追う従来の解除を避けられるか」。今回の評価は探索的であり、結果を見た後の解析拡張と公開I/O監査を含む。事前登録実験ではない。

型`C`はmutableな参照fieldを一つ持つCell、型`P`は二つのC参照をimmutableに保持するPair。Pairの意味を`bit(p) = (p.left == p.right)`とする。Cellのfield内容はscratch領域であり、bitの意味に含めない。

```text
NAND(p, q):
    a, b <- 異なるfresh Cell
    q.left.field  <- a
    q.right.field <- b
    u <- q.left.field
    p.left.field  <- a
    p.right.field <- u
    return Pair(a, p.left.field)
```

qのbitが1ならu=b、それ以外はu=a。pのbitが1なら最終field=u、それ以外はa。返した二参照が等しいのは、pとqが両方1の場合以外であり、NANDとなる。pとqのCellが交差して共有されていても、uを先にlocalへ退避するため成立する。mutableなfieldを書き換えても、以前のPairの参照同一性は変化しない。

入力のbitをPairへ変換し、AND/OR/XORと加算のcarryをNAND回路へ展開する。定数rotateはbit列の並べ替え。gate間ではBooleanへ復号せず、最後の32bitを`ref.eq`で戻す。新しい参照の総数はgate数に従って増えるが、この事実だけでは解析が難しくなるとは限らない。

## 実装と意味保存の範囲

`compile.py INPUT.wasm OUTPUT.wasm`は実バイナリをWABTで読み、単一のpure i32関数を変換する。許可するのはi32引数、定数、AND/OR/XOR/ADD、定数ROTL。唯一のexportを`run`とし、memory、import、global、table、call、loop、除算、浮動小数点、副作用などは拒否する。任意Wasm用のパスではない。

GC出力はBinaryen 133のassemblerと既定validationを使用する。機能はMVP＋reference-types＋GCに限定する。Node/V8でも全出力をvalidateして実行した。WABTは元のMVP入力と回復したMVP回路の検証に使い、GC出力をWABT interpreterで検証したとは主張しない。

NANDの同一性不変式、bit回路の合成、32bit剰余加算により意図した返り値を保存する。参照は非公開で、ホストcallback・共有・再入はない。元入力にtrapを起こす演算はない。追加allocationによる資源枯渇、実行時間、GC動作は同値性の対象外である。この制約は実用上重要であり、資源を含む任意の文脈で同値とは言わない。実装全体の形式証明はしていない。

## 方式既知の解析

攻撃`attack.py`が受け取るのは変換後.wasmだけであり、元の式・生成DAG・対応表・中間値oracleは渡さない。公開された表現規則と限定profileは知る。

まず、二つのPairの四つのCell端点について、同じ参照をどれに割り当てるかという全15個の集合分割を列挙し、バイナリから抽出したhelperのfield更新を評価する。事前のscratch値を読む構成は拒否する。fresh identityを名前替えしても挙動が変わらないこのprofileでは、具体アドレスを列挙する必要がない。全パターンでNAND関係を確認してから、Pairを1bitへ置き換える。

最適化後のlocal再利用・tee・blockと、inline化された入力／出力変換にも対応した。出力はGC命令・型を持たない実行可能なi32回路である。**元のword単位の式まで高位化した結果とは区別する。** 一般のheap推論器でもない。

135回の追加native実行（9条件×15共有パターン）でhelper関係を検査した。常に1を返す変異gate、誤ったdecoder、事前scratch読み出しを含む3対照は拒否した。部分的な抽象評価器の正しさを任意GCプログラムへ一般化しない。

## 結果

正規の結果は[`alias-circuit-v4/`](../../results/invention-20261018/alias-circuit-v4/)。入力・変換出力・回復出力・manifest・元コードsnapshot・全測定値を保存した。

- 3個の小さい32bit kernel × 元／GC × raw/O2/O3で18条件。さらにGCの全9条件から回復したscalar回路を加え、27条件を検査。
- 各4,288入力（境界の直積64、walking bit 128、seed固定random 4,096）を独立JS参照計算へ照合。計115,776実行、不一致0。全2^64入力の実行検査ではない。
- **9 / 9条件で回路を回復**。攻撃時間はバイナリ読取・外部tool・回復出力のvalidationを含む単発値で約62–96ms。純粋な推論時間の反復測定ではない。
- 各入力は544 / 544 / 608 NAND gateへ展開された。変換時間はそれぞれ約80 / 81 / 84ms。対象のサイズによる一般的な計算量・実時間の評価はしていない。

性能は各条件を3回、別Node processで実行した。4,000回warm-up、2,000呼出し×11回を測定。各processの中央値を求め、その3値の中央値を下表に示す。JS→Wasm呼出しを含む。全条件・ばらつきは[`comparison.md`](../../results/invention-20261018/alias-circuit-v4/comparison.md)、生データは`checks.json`。

|kernel（入力O3）|元 ns / bytes|GC ns / bytes|回復回路 ns / bytes|
|---|---:|---:|---:|
|mix|20.40 / 47|4,904.25 / 5,496|175.35 / 6,551|
|carry|20.20 / 47|4,813.10 / 5,426|177.80 / 6,529|
|mask|20.95 / 54|5,163.50 / 6,002|182.85 / 7,431|

「回復回路」はO3入力から出した回路で、回復後にもう一度O3を適用したものではない。同一bit回路からGC表現を除いた対照であり、費用を一致させた先行方式比較ではない。GC側のこの測定値は元の約238–246倍で、耐性の改善は確認できなかった。対照が非常に小さく呼出し費用の割合が大きいため、実製品の倍率を予測しない。

process peak RSSの中央値は、元約43.7–43.8MiB、GC約52.6–53.1MiB、回復約44.4–44.5MiB。Node・JIT・GC・測定器を含み、対象heapだけの使用量ではない。線形memoryは全て0。過去の`checks.json`の`heap_after_gc`というfieldは測定loop後のheap値であり、GC直後の保持heapを意味しない。報告値には使わず、今後のコードでは`heap_after_timed_calls`に訂正した。

## 公開I/O監査

これらの小さいkernelを実用的な保護強度の主評価に使うことも避ける。`audit-io.cjs`には公開oracleだけを渡し、add/xor/and/orとrotateを含む5,120個の式templateを探索した。定数候補の一つは公開`run(0,0)`の値から得る。16訓練入力と256 holdout入力、計272問い合わせで、元／GCの全18条件に一致する短い式を得た。

探索した候補数はmix 72、carry 302、mask 1,604。学習した式は事後採点で元のpure i32式とZ3照合し、全18件で不等式がunsatとなった。これは取り出した式同士の全32bit入力での一致であり、GC変換器全体の正当性証明ではない。

この文法はfixtureを見た後に構成した適応的な限定攻撃であり、一般の未知プログラムに対する無偏な学習性能ではない。ただし実際に問い合わせだけで一致式を得られるという上界は成立する。今回のfixtureは変換・攻撃の動作確認に使い、その公開入出力の学習を難読化で防げるとの成功条件は置かない。公開I/Oで簡単に解ける対象を再び主評価へ採用しないための監査である。

## 先行研究との差と採否

1. Christian Collberg, Clark Thomborson, Douglas Low, *Manufacturing Cheap, Resilient, and Stealthy Opaque Constructs*, POPL 1998, pp.184–196, [DOI 10.1145/268946.268962](https://doi.org/10.1145/268946.268962)。査読会議論文。出版社の書誌・要旨、著者PDFの検索索引にある§5.1の断片を確認。alias関係と動的構造の不変式をopaque predicateへ使う。今回の入力依存NANDは常に既知の真偽値を持つpredicateとは異なるが、参照共有を難化に使う原理は先行する。全文の評価値は今回未確認で、実装比較はしていない。
2. Chenxi Wang, Jonathan Hill, John Knight, Jack Davidson, *Software Tamper Resistance: Obstructing Static Analysis of Programs*, University of Virginia CS-2000-12, 2000, 技術報告、[機関記録／DOI](https://doi.org/10.18130/V36T9V)。要旨と書誌を確認。alias導入と制御・データ解析の相互依存を扱う。本文URLはbot確認で取得できず、検索索引にあるBoolean assignmentのalias表現を、全文を読んだ詳細比較と扱わない。最悪時のNP-hardnessを今回の小さいhelperの難しさへ転用しない。
3. Stephen Drape, *Obfuscation of Abstract Data-Types*, Oxford博士論文、2004、[本文](https://www.cs.ox.ac.uk/files/2892/thesis.pdf)。以前確認した抽象表現と演算の置換が一般的な比較先。今回の具体的なNAND構成が同一かは未確認であり、重複が見つからないことを新規性の証拠にしない。
4. WebAssembly Community Group, [GC overview](https://github.com/WebAssembly/spec/blob/main/proposals/gc/Overview.md)、技術資料。structのmutable field、参照同一性、GC管理を確認した。このoverviewには歴史的・将来提案も混在するため、掲載された全機能を現行標準と見なさない。本実装の利用機能はBinaryenとNodeで個別に検証した。

Wasmとの関係は、linear-memoryの数値アドレスを必要とせず、型付きGC参照とfield更新だけで実行する点である。ただし同じ原理は他の安全な参照言語にも移せる。Wasm命令へ移植したことだけでは独立した新規性にならない。

最大のReject理由は、既知のalias/ADT表現からの独立した差を示せず、freshな具体identityの多さが小さな等値関係への縮約を防がないこと。9条件の回復と大きな実行費用を踏まえ、この構成のseedやallocation数だけを変える追加試作はしない。一般の全GC難読化が無効だという結論ではない。研究全体は継続中。

## 再現

rootから新しい出力先を指定する。Node、Python 3.9、WABT 1.0.42、Binaryen 133が必要。既存出力を上書きしない。`.tools`の別配置は`WASM_TOOLS_ROOT`。SMT照合には`.tools/encoding-synthesis-python`のz3-solverを使う（この環境は4.13.3）。

```powershell
python research/alias-circuit/experiment.py results/invention-20261018/alias-reproduction
node research/alias-circuit/check.cjs results/invention-20261018/alias-reproduction
python research/alias-circuit/check_quotient.py results/invention-20261018/alias-reproduction
node research/alias-circuit/audit-io.cjs results/invention-20261018/alias-reproduction
python research/alias-circuit/verify_io.py results/invention-20261018/alias-reproduction
python research/alias-circuit/report.py results/invention-20261018/alias-reproduction
```

単体変換と解除:

```powershell
python research/alias-circuit/compile.py input.wasm alias.wasm
python research/alias-circuit/attack.py alias.wasm recovered.wasm
```

初期試作v1は存在しないBinaryen flag `--validate`の指定で停止した。v2は`--all-features`によって最適化時にNode未対応のexact referenceを出力した。v3では対象機能を訂正したが、解除器が`drop`を未対応としていた。v4で修正した。これらは実装・測定の修正であり、難読化が解析に勝った結果ではない。古い出力を保存して区別した。
