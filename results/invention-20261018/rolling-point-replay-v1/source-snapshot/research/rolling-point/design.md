# 固定文字列の群上rolling照合：既知原理の適用限界を調べる

2026-10-18、実装前に固定。これは新発明として採用した方式ではない。
前回の射影では公開APIから簡潔な等価実装を得られた。今回は、出力が一致位置だけである固定文字列照合を使い、保護する資産を「未提供のpattern」と明示する。一般アルゴリズムの秘匿、clone防止とは区別する。

## 先行性と判断

群要素 `(g, g^s)` で秘密の一致対象sを置き換える方式は既知である。Allison Bishop, Lucas Kowalczyk, Tal Malkin, Valerio Pastro, Mariana Raykova, Kevin Shi, *In Pursuit of Clarity In Obfuscation*, IACR ePrint 2019/463, pp.4–6の説明を確認した。[本文](https://eprint.iacr.org/2019/463.pdf)、[書誌](https://eprint.iacr.org/2019/463)。プレプリント／解説として扱い、本稿から新しい安全性定理を借用しない。

Lynn, Prabhakaran, Sahai, *Positive Results and Techniques for Obfuscation*, EUROCRYPT 2004, DOI10.1007/978-3-540-24676-3_2, §4, §6を確認。[本文](https://iacr.org/archive/eurocrypt2004/30270019/ob.pdf)。random oracleでの点関数と合成が先行する。本文は近似的機能保存を扱う。今回のexact bounded-domain equalityとは条件が異なるが、点関数という原理は新しくない。

Galbraith, Zobernig, *Obfuscating Finite Automata*, SAC 2020（改訂会議録2021）, DOI10.1007/978-3-030-81652-0_4。[会議preproceedings](https://sacworkshop.org/SAC20/files/preproceedings/10-FiniteAutomata.pdf)の§1, §4–5, §7–8を確認。evasive DFAを行列encodingとzero testで扱い、入力長上限と新しい計算量仮定が必要。秘密substringは既に対象。一般DFAに対する方式と今回の単一固定文字列を同列に優劣比較しない。本体は未実行。

従って「群上の線形rolling更新」と「点関数」を結合するだけでは、要求された独立の新原理とは数えない。今回の実装は新規性未確立の候補を膨らませるためでなく、exact semanticsと実コストの制約を具体化する比較部品である。研究goalの完了とはしない。

## 規則

RFC3526 §3の2048bit safe prime p、q=(p-1)/2、g=2を使用する。gの位数はq。公開長Lは1..255 byte。byte列のbig-endian整数をvとすると、0 <= v < 256^L < qなのでg^vの比較はこの領域で完全一致である。公開する秘密依存値はT=g^patternのみ。

窓wを1byte進め、先頭aを除きbを加えると

`v' = 256*v - a*256^L + b`

である。従って `H' = H^256 * D[a] * A[b] mod p`、`D[a]=g^(-a*256^L mod q)`、`A[b]=g^b`。最初のL byteまではDを掛けない。最初にH==Tになる位置を返す。L未満は-1。

### Wasmとの関係と意味保存

実.wasmをWABTで読み、正規の固定文字列scan templateとのAST全体一致を確認して変換する。任意のstrstr、最適化済み任意コード、regex、複数patternへの変換を主張しない。入力はexportされた固定1page memory32。run(ptr,len)はunsigned 64bitで範囲を検査し、範囲外ならmemory load trap、正常なら最初のoffsetか-1。公開memoryは一切変更しない。

作業表・Montgomery scratchはWasmの非export第2memoryへ置く。これにより公開memoryのsize、grow(0)、全byteを保存する。追加の私有memory使用量は性能コストに数える。multi-memory未対応はunsupportedであり、解析耐性とは数えない。時間・stack trace・資源枯渇の同一性は契約に含めない。

Wasm i64で32bit limbのschoolbook積とMontgomery REDCを実装する。最大 `(B-1)^2+2*(B-1)=B^2-1` (B=2^32) の加算なので、その内側積のunsigned i64はwrapしない。carry伝播・最後の条件減算を別途検査する。暗号実装として監査済みとは主張しない。[multi-memory命令仕様](https://webassembly.github.io/multi-memory/core/exec/instructions.html)と[RFC3526 §3](https://www.rfc-editor.org/rfc/rfc3526.html#section-3)を参照した。

### 回避できない制約

固定幅wordのwrapをそのまま指数のwrapとして実装することはできない。Z/(2^w)から群への加法準同型で全wordの等値を保存するなら、像の位数は2^wでなければならない。2冪位数の離散対数はPohlig–Hellman型のbitごとの回復で安く解ける。今回の大きな素数位数群はword全域の同態的代替ではなく、長さ制約によりwrapしないencodingを選んでいる。

先行するsmooth-order logarithmの根拠はStephen C. Pohlig, Martin E. Hellman, *An Improved Algorithm for Computing Logarithms over GF(p) and Its Cryptographic Significance*, IEEE Transactions on Information Theory 24(1), 106–110, 1978, DOI10.1109/TIT.1978.1055817。[著者公開本文](https://ee.stanford.edu/~hellman/publications/28.pdf)の導入と§III–Vの対数回復・small factorsの議論を照合した。上の制約整理を新しい暗号学的定理とはしない。

## 攻撃・成功判定

解析者は方式、p,g,L、全Wasm、全定数、内部値、任意の公開入力を利用できる。実験の正解patternや生成seedを攻撃入力に渡さない。一致する入力を一度持てば、そのwindowからpatternが分かる。低entropy辞書、既知prefix/suffix、meet-in-the-middle／interval DLogは独立に検査する。DLPだけから一般的VBBや任意の分布での保護を主張しない。

比較はplain、全windowでg^vを再計算するpoint方式、rolling方式。前二者に対する正確な意味保存、raw/O2/O3、公開memory・trapを検査する。性能はwarmup後のfresh-process反復、bytes、private memory、peak RSS、変換時間。rollingが再計算より速くても新規性・総合的な保護優位の証明にはしない。

次の採用案に進む条件は、既知point方式を越える新しい構成規則と保護対象を説明できること。単なる窓更新の高速化だけなら、この枝は比較部品で止める。
