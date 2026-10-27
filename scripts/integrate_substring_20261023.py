# -*- coding: utf-8 -*-
"""Integrate measured results without modifying the pre-existing TeX changes."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
marker='## 部分文字列をまたぐ文法変換と三次係数からの解除（2026-10-23）'
items={
 'research/literature-review.md':'[substring-shearの文献照合](substring-shear/prior-art.md)を追加。CohenらACL2012のテンソル内側計算、RabusseauらAISTATS2016のWTA、BonsangueらCMCS2012のproper algebraic system、HriljacのWO2012040383A1と照合した。読了範囲と未読の評価を分け、検索に現れなかったことを新規性の証拠にしない。',
 'research/research-gap.md':'単一セルの混合から、全分割点をまたぐ非線形な級数変換へ移した。内部値の照会APIを置かないparserで検査したが、[三次係数の合同式](substring-shear/algorithm.md)から短い文法を回復できた。非線形化・非局所化だけでなく、生成規則が露出させる低次数の恒等式を先に検査することが次案の必要条件となる。',
 'research/candidates.md':'[部分文字列の畳み込みshear](substring-shear/README.md)を実装・評価。線形テンソル変換とは異なるspanを混ぜるが、既知の非線形座標変換・形式級数変換からの独立した生成規則は未確立。正当性と方式既知の回復を実装できた。最大のReject理由は、係数を任意32bit値にしても公開三次成分から安く解除できる点。主54条件・四次追加12条件すべてを回復し、主特許候補には不採用。',
 'research/threat-model.md':'substring-shearでは、可変長文字列の重み付きparse countを返すprivate memoryのWasmを配布する。解析者はbinaryと方式を知るが、元文法、変換座標、係数、seedは渡されない。保護対象は簡潔な文法規則。元の名前・重みそのものを戻せなくても、少数規則の等価文法へ戻れば攻撃成功とする。一般の逆コンパイラの成功率や暗号的秘匿へは一般化しない。',
 'research/algorithm.md':'[生成手順と証明](substring-shear/algorithm.md)。X=A+Q(X)に対し、Y_a=X_a+α X_bX_c、G(Y)=A+Q(Y−αe_aY_bY_c)+αe_aY_bY_cを展開・二項化する。aは開始変数と異なり、b,cはaと異なる。propernessから意味を保存する。一方、三次成分の線形合同式を解けば、任意の重みでも最小剰余一つの逆shearで二項文法へ戻せる。変換と解除の両方をCLI化した。',
 'research/novelty-analysis.md':'[今回の先行性評価](substring-shear/prior-art.md)。線形な同一spanの混合と異なる点はあるが、既知の多項式座標変換と形式級数系の枠組みを超えた保護上の利点は得られなかった。単一二次shearの安い回復条件は具体的に論証した。主発明の新規性・特許性の確立とはしない。係数の変更だけでこの案を継続しない。',
 'research/experiments.md':'[実測レポート](../results/invention-20261023/substring-shear-report-v1/report.md)。主120本49,640呼出し、四次追加28本9,968呼出し、不一致0。診断66本27,302呼出しでtrap前後の全memory不変、別WABT330呼出し一致。回復は主54/54、追加12/12。主3文法の実行時間は元の約1.43〜1.65倍、108process/756batch。有限系432件と小幅算術5,460対も検査。旧不完全run、再利用した入力、未測定範囲を区別した。',
 'paper-draft.md':'**Proposed Method / Implementation.** 全分割点を通る非線形な部分文字列表現を、properな重み付き文法の多項式置換と二項化から生成した。限定profileの実Wasmを受け取るCLIを作成した。\n\n**Evaluation.** 主120本49,640呼出しと、四次項が非ゼロとなる追加28本9,968呼出しは参照実装と一致。未変換、線形、非線形、回復後を比較し、非線形版の実行時間は約1.43〜1.65倍。主54条件と追加12条件はすべて等価な簡潔な文法へ回復できた。\n\n**Discussion / Limitations / Conclusion.** 単一二次shearが作る三次係数は、任意の32bit重みでも逆変換を求める線形合同式を露出させる。非可換性を使い、最小剰余の候補だけで四次も消えることを論証した。一般Wasm・実用parser・既存製品との同コスト比較には未到達。主発明としては不採用であり、新規性や特許性の確立とは扱わない。[設計と再現](research/substring-shear/README.md)、[実測](results/invention-20261023/substring-shear-report-v1/report.md)。',
 'research/novelty-status-20261023.md':'[部分文字列をまたぐ文法変換](substring-shear/README.md)を実装・反証した。主120本49,640呼出し、四次追加28本9,968呼出しで不一致0。主54+追加12条件は公開係数だけからすべて回復でき、単一shearの係数変更では解消しない理由も論証した。実行時間約1.43〜1.65倍に対する保護優位がなく、主特許候補には不採用。新しい有力な発明はまだ確立していない。',
}
for path,body in items.items():
    dst=ROOT/path;text=dst.read_text(encoding='utf-8')
    if marker not in text:dst.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+body+'\n',encoding='utf-8')
dst=ROOT/'research/novelty-status-20261023.md';text=dst.read_text(encoding='utf-8')
text=text.replace('16%使用（約84%残）','18%使用（約82%残）')
dst.write_text(text,encoding='utf-8')
dst=ROOT/'README.md';text=dst.read_text(encoding='utf-8')
line='2026-10-23追補：[部分文字列をまたぐ非線形な文法変換](research/substring-shear/README.md)を実Wasmで検証。主120本49,640呼出し、四次追加28本9,968呼出しは一致したが、公開係数から主54+追加12条件すべてを回復。任意の重みにも通用する解除条件を論証し、実行時間約1.43〜1.65倍の本案は主特許候補に不採用。[実測・再現](results/invention-20261023/substring-shear-report-v1/report.md)。'
if line not in text:text=text.replace('# webassembly_obfuscation\n','# webassembly_obfuscation\n\n'+line+'\n',1)
dst.write_text(text,encoding='utf-8')
print('Updated research documents and README; left paper/main.tex and paper/README.md untouched.')
