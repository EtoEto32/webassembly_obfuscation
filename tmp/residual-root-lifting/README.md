# 残差方式の実行規則と既存定理の適用範囲

## 結論

前回の96生成例について、残差式の係数を知らなくても、式を評価するoracleがあれば32ビットの零点を32回の更新と1回の確認で求められた。全34,176組で一致した。ただしこれは**正規の計算手順**であり、元ソースを復元した、難読化を解いたという結果ではない。前回の係数恒等式による簡約と区別する。

零点を段階的に求めることは既知のHensel型の手法であり、新しい難読化原理として採用しない。この族の係数調整を新規候補として増やす作業はここで終了する。他の具体的な規則が未設計であるため、全体目標は未達成。

## 今回の導出

前回と同じ族を考える。

    a=z-F, b=t-G
    Q1=a+a(a+1)b R1(a,b)
    Q2=b+b(b+1)a R2(a,b)

Q mod2=(a,b)なので、Q(0,0)の下位ビットでF,Gの下位ビットが得られる。一度このビットが合うとa,bは偶数であり、Qのヤコビ行列はmod2で単位行列になる。

k>=1でQ(z,t)=0 mod2^kなら、z,tの第kビットをQ(z,t)の第kビットで修正すると、Q=0 mod2^(k+1)となる。これは多項式のTaylor展開で、二次以上の修正項が2^(2k)の倍数となることから従う。k=0の場合は前述のparity関係を直接使う。従ってw回でmod2^wの零点を得られる。

コードは下位kビットを確定し、未設定の第kビットをORで設定する。更新時に上位ビットは0なので加算と同じである。R1/R2の値、次数、F/Gはliftへ渡さない。oracleの内部には検証用F/Gがあるが、liftからその状態は参照していない。別プロセスの盲検実験ではない。

この説明は本族に限る。任意多項式の根、任意Wasmの実行、隠れたsource式の復元を解くものではない。またoracle1回の実行費用は式に依存するため、「32回」を一定の実行時間と解釈しない。

## 実測

- 前回の96生成例（92種類）を読み取り使用。
- w=1..4で各候補の全F,Gを確認: 32,640組。
- w=32で各候補16組、別の固定シード: 1,536組。
- 合計34,176組、未一致0。最終確認を含むoracle評価203,520回。
- Python 3.12.14、標準ライブラリのみ。入力シード、元の結果SHA256、コードSHA256はresults.json。

小幅入力は全列挙であり乱数入力とは数えない。32ビットは有限個の入力による照合。上の帰納的説明と実装検査は区別する。今回はWasm、性能比較、一般的な逆コンパイルを実装していない。

## 一次資料との照合

1. Dvir, Oliveira, Shpilka, *Testing Equivalence of Polynomials under Shifts*, arXiv:1401.3714v2 (2014-02-19)。§1、定理1.5–1.6、§2の前提を確認。定理は標数0または次数より大きい標数の**体**を扱う。Z/(2^32)Zは体ではないため、これを本候補全体の多項式時間復元の証明として引用しない。
   https://arxiv.org/pdf/1401.3714

2. Chillara, Grichener, Shpilka, *On Hardness of Testing Equivalence to Sparse Polynomials Under Shifts*, STACS2023。導入の問題定義、整域の前提、定理1を確認。疎化するシフトを探す問題と、既知の2式を対応させる問題は別であり、この硬さを本族の保護根拠にはできない。他の定理すべてを読んだとは扱わない。
   https://drops.dagstuhl.de/storage/00lipics/lipics-vol254-stacs2023/LIPIcs.STACS.2023.22/LIPIcs.STACS.2023.22.pdf

3. Keith Conrad, *A Multivariable Hensel's Lemma*。定理3.3とNewton更新の説明を確認。刊行年はPDFから確定していない。2026-10-12閲覧。今回の固定1ビット更新は本族のmod2ヤコビ行列を使う直接の導出であり、本文の一般Newton実装を再現したものではない。
   https://kconrad.math.uconn.edu/blurbs/gradnumthy/multivarhensel.pdf

検索: polynomial shift equivalence testing hidden shift multivariate polynomial Kayal / polynomial shift equivalence finite characteristic ring modulo powers two / multivariable Hensel lemma invertible Jacobian p adic Keith Conrad pdf。

## 再現

空ディレクトリにlift.pyとcheck.pyをコピーし、Pythonで次を実行する。既存results.jsonがあれば停止する。

    python check.py C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/residual-family-search/results.json

元のCSEC原稿・実験は変更しない。新しいアルゴリズムの目標を実行器や復元器の作成に変更したものではない。
