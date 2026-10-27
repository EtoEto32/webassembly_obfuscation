# 近い先行技術との対応

調査日2026-10-23。検索語：span program obfuscation input dependent basis、polynomial row column matrix obfuscation、bitsliced Gaussian elimination。下記は実際に確認した範囲。未発見を新規性の証明にしない。

|一次資料|種別・書誌|読めた箇所|今回への含意|
|---|---|---|---|
|[On Span Programs](https://www.math.ias.edu/~avi/PUBLICATIONS/MYPAPERS/KW93/proc.pdf)|Mauricio Karchmer, Avi Wigderson, 1993, 8th Structure in Complexity Theory, pp.102–111, DOI 10.1109/SCT.1993.336536。査読会議論文|§3定義・基底変更・Theorem 2/3構成、§4 Theorem 5と証明、§5 Def.3/Theorem 6。全ての下界証明を読了したとはしない|線形包によるBoolean関数表現は既知。グラフ接続のspan表現も明示され、以前の接続グラフ案との近さがある。実行速度の実験論文ではない。|
|[Securing accessible systems using cross-linking](https://patents.google.com/patent/EP2831791B1/en)|Harold Johnson, Yuan Xiang Gu, Michael Wiener。EP2831791B1、優先日表示2012-03-30、A1公開2015-02-04、B1公開2020-10-21。特許公報|C7 Proposition 7の生成手順とRemarks 2–4、書誌。請求項全体やfamilyの法的評価は未実施|文脈の変数を係数にした行・列操作による可逆行列生成が具体的に記載される。「入力依存基底だから新しい」とは言えない。|
|[LOKI: Hardening Code Obfuscation Against Automated Attacks](https://www.usenix.org/conference/usenixsecurity22/presentation/schloegel)|Moritz Schloegel, Tim Blazytko, Moritz Contag, Cornelius Aschermann, Julius Basler, Thorsten Holz, Ali Abbasi。USENIX Security 2022, pp.3055–3073。査読会議論文|著者公開PDFのabstract、§4.5 superoperators、§4.7 verification、§5 implementation|局所的な意味の回復を防ぐ統合と方式既知の攻撃への評価は既存課題。今回の実験値をLOKIとの優劣比較に使わない。|

Nikov/Nikovaの *New Monotone Span Programs from Old*（ePrint 2004/282）は関連検索に出たがPDF取得が403だった。本文を読めていないため内容を補完せず、上表の根拠には使わない。一般のbitslicing・Gaussian eliminationも既知であり、今回の32lane kernelをそれだけで新発明と主張しない。

## 技術的な差と、それが足りない理由

今回の具体化は、ラベルを行係数へ吸収し、行とtargetを含む列を入力依存shearで展開し、32laneのWasm evaluatorを生成する。span理論の表現方法、既知の可逆多項式行列生成、bit並列実装のそれぞれを使っている。これらをWasmで実行したことは確認できるが、既存技術の直接的な適用を超える生成上の差を示せていない。

レビューで最も大きいReject理由は、構成の近さと、適応解析に対する費用対効果の弱さである。今回の否定結果は特許の有効性・侵害・取得可否を判断したものではなく、自分たちの研究候補を採用しない技術判断である。
