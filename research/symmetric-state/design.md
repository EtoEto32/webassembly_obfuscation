# 内部状態を対称式へ縮約する候補：事前設計

2026-10-18。可変tableの小さい商が解除を容易にした反証から、逆向きに「元の具体状態を捨て、出力に必要な商だけで計算する」案を調べる。符号化した元状態を保持する前案とは異なる。ただし数学的原理は既知であり、新規アルゴリズムとは未認定。

## 変換規則

純粋なi32多項式反復 (x,y)←(f(x,y),f(y,x)) と、対称な最終観測h(x,y)を対象とする。整数多項式として恒等式を求め、Wasmではmod 2^32で評価する。

1. 入力.wasmを型検査し、privateな2入力2出力stepと固定形のrun driverを認識する。
2. stepの二つの多項式が交換同変であること、hが対称であることを確認する。
3. s=x+y,p=xyとして f(x,y)+f(y,x)=S(s,p)、f(x,y)f(y,x)=P(s,p)、h(x,y)=H(s,p)を対称式の標準的な算法で求める。
4. stepを(S,P)へ置き換え、run入口で(s,p)を構成し、出口をHにする。多値返却により同時更新する。
5. 非対称出力、元のx/yの外部観測、副作用、trap、非多項式命令、認識外のdriverは拒否する。

α(x,y)=(x+y,xy) とすれば α∘F=F♯∘α、h=H∘α。これは可逆符号化ではない。特にZ/(2^32)では零因子のため、同じ(s,p)が単なる交換以外の組にも対応し得る。整数恒等式から剰余環へ移すことと、環上で逆関数が存在することを混同しない。

Wasmとの関係は、定義された整数wrapとmulti-valueによる同時更新、実バイナリ上の認識である。原理は他の固定幅形式でも成立し、Wasm固有の新規性は弱い。先に検討したGC型分派・関数signature統一は既知手法と重なるため再実装しない。

## 仮説・攻撃・反証条件

保護課題は一時点のsnapshotから元x/yを推測することではなく、公開バイナリから元の対になった更新則を回復すること。攻撃者は方式を知り、入力と全コードを見られる。秘密は仮定しない。元コード、生成時manifestは解除器へ与えない。

反証攻撃を先に固定する：S(s,p),P(s,p)を抽出し、s=x+y,p=xyを代入する。z²−S(x+y,xy)z+P(x+y,xy)を多項式因数分解して、z−f(x,y)とz−f(y,x)が得られるか調べる。得られれば非単射な具体値の表現でも更新アルゴリズムは隠せない。係数の整数持上げが合わない場合やoptimizerの構文未対応は、攻撃失敗と耐性成立を区別する。元の二つの役割の交換は対称出力に影響しないので、交換までの復元を成功と数える。

少なくとも3つの異なる多項式更新則、raw/O2/O3、元/縮約/解除を比較する。人工kernelであって実アプリではない。境界入力・乱数・反復回数0を含める。小さいbit幅では全状態の衝突を列挙し、「snapshot非一意性」と「更新則復元」を別々に測る。新規性または保護効果が反証された場合、性能を大規模測定して採用を装わない。

## 近接研究と未確認範囲

- Roberto Giacobazzi, Neil D. Jones, Isabella Mastroeni, *Obfuscation by Partial Evaluation of Distorted Interpreters*, PEPM 2012, pp.63–72, DOI [10.1145/2103746.2103761](https://doi.org/10.1145/2103746.2103761)。査読済みworkshop論文。[所属大学の書誌・要旨](https://experts.arizona.edu/en/publications/obfuscation-by-partial-evaluation-of-distorted-interpreters/) と作者PDFの検索取得§5.5を確認。データ表現と抽象解釈による難読化は既知。§5.5は復号で元のデータへ戻す条件を記す。本案は最終観測だけを保存し途中の元データを戻さないが、抽象解釈の新理論とは主張しない。PDF全体の直接取得は失敗しており、全文を読んだとはしない。
- Enric Rodríguez-Carbonell, Deepak Kapur, *An Abstract Interpretation Approach for Automatic Generation of Polynomial Invariants*, SAS 2004, DOI [10.1007/978-3-540-27864-1_21](https://doi.org/10.1007/978-3-540-27864-1_21)。査読済み会議論文。[作者書誌](https://www.cs.upc.edu/~erodri/conference_papers.html) と作者PDFの検索取得要旨を確認。多項式不変条件・idealによる解析の先行例。直接PDF取得失敗、比較実験の数値は未確認。
- [SymPy公式symmetrize資料](https://docs.sympy.org/latest/modules/polys/reference.html#sympy.polys.polyfuncs.symmetrize) を確認。基本対称式への変換は既製の算法であり、今回の発明とは数えない。
- [Wasm 3.0型仕様](https://webassembly.github.io/spec/core/syntax/types.html)を確認。多値型の利用自体は既存機能。

検索語：program obfuscation symmetric polynomials invariant quotient abstract interpretation / data obfuscation non injective abstract interpretation / program transformation elementary symmetric polynomials recurrence。現時点で本構成と完全同一の論文を同定できていないが、それは新規性の証明ではない。最大のReject理由は、既知の意味的抽象化を狭い多項式族へ適用しただけで、さらに因数分解で元更新則が露出すること。
