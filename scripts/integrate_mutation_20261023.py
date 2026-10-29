# -*- coding: utf-8 -*-
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
marker='## 更新状態の商と公開更新による回復（2026-10-23）'
entries={
 'research/literature-review.md':'[更新状態の先行性](mutation-quotient/prior-art.md)を追加。HawkinsほかPLDI2011の著者PDFの導入・§4.1–4.2、Wahl/DonaldsonのSymmetry2010の著者PDFの導入・§5.4冒頭、Wasm公式relaxed laneselect仕様を確認した。商・代表状態・表現合成という一般原理の先行性と、今回の限定した合同条件を区別する。特許の請求項全文との対応は未精査。',
 'research/research-gap.md':'[更新可能な商状態](mutation-quotient/README.md)では、readonlyで消せる共通の絶対値が、公開scale更新によって再び観測可能になる。消去可能量は配列全体でd=min(32,nu_2(k-1)) bitであり、各セルd bitではない。情報を消しただけでは、短い等価な処理への回復を妨げない。次の設計は公開APIから元の内部値をほぼ直接得られる課題に限定せず、対象処理の観測契約に沿って選ぶ必要がある。',
 'research/candidates.md':'[mutation-quotient](mutation-quotient/README.md)を実装・反証。共通加算で同値な状態をまとめ、更新操作から安全に消せるビット数を決める案。canonicalとrepresentativeを比較したが、全54対照・変換条件を公開I/Oから回復した。商・合同算術という先行原理から独立した差が弱く、主特許候補には不採用。既存readonly試作の成立範囲を広げた検査であり、別原理の新発明数へ水増ししない。先行したrelaxed laneselectの関係制約案も仕様の片側への固定で除外した。',
 'research/threat-model.md':'今回の[公開I/O攻撃](mutation-quotient/algorithm.md)は、差の照会、加算、相対コピー、定数k倍、resetの公開APIとschema n,kを知る。攻撃関数へ元初期値やseedを与えず、採点だけに元状態を使う。内部memoryをexportした診断版は正当性検査用で、攻撃には使わない。配列長n回の問い合わせで代表状態を回復する結果を、集約結果しか返さない別APIへ一般化しない。',
 'research/algorithm.md':'[更新状態商の設計・擬似コード](mutation-quotient/algorithm.md)。任意長の同じ操作列に対する二状態の観測同値性は、y=x+c*1かつ(k-1)c=0 mod2^32と必要十分に分類できる。canonicalで毎回正規化する実装と、初期代表を選んで元の更新コードを保つ実装を用意した。これは動く限定変換であり、新しい主難読化算法の採用ではない。',
 'research/novelty-analysis.md':'[今回の先行性と判断](mutation-quotient/prior-art.md)。有限環の消去精度と公開更新による回復の具体条件は論証・実測したが、商状態・対称性・表現合成という既知枠組みとの差が弱い。代表版のrun本体はraw/O3全18条件で未変換と同じで、canonicalの追加費用にも保護優位を確認できなかった。独立した有力な特許候補の確立とは扱わない。',
 'research/experiments.md':'[実測・証拠823ファイル](../results/invention-20261023/mutation-quotient-report-v1/report.md)。主90本448,230呼出し（trap16,110）、診断54本268,938呼出し（trap9,666）、I/O回復54本268,938呼出しが一致。WABT324呼出し、90本byte再生成、6件SMT閉性、小幅1,118,464比較も確認。36 fresh process/252batchでcanonicalは元の約1.58〜1.78倍、representativeは約0.998〜1.013倍。linear memoryは全版64KiB。入力再利用・サイズ違いを独立ベンチマーク数にしない。',
 'paper-draft.md':'更新可能な配列の共通加算を忘れる状態商を、実Wasmに実装した。公開された差の照会・加算・コピー・定数k倍のAPIでは、失ってよい情報量が配列全体でmin(32,nu_2(k-1)) bitに制限される。元の絶対状態が一意に戻らなくても、配列長n回の公開問い合わせで短い等価な状態機械を回復できることを構成した。主90本448,230呼出しは一致したが、canonical実装には約1.58〜1.78倍の費用があり、元命令を保つ代表実装でも同じ情報消去を達成した。[成立条件](research/mutation-quotient/algorithm.md)と[実測](results/invention-20261023/mutation-quotient-report-v1/report.md)を保存し、情報消去と算法保護の違いを負の結果として扱う。商・対称性縮約以上の新規性、特許性、実用上の保護優位は未確立である。',
}
for name,body in entries.items():
    f=ROOT/name;text=f.read_text(encoding='utf-8')
    if marker not in text:f.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+body+'\n',encoding='utf-8')
f=ROOT/'README.md';text=f.read_text(encoding='utf-8')
notice='2026-10-23追補：[更新を含む情報消去の成立条件と反証](research/mutation-quotient/README.md)を実Wasmへ実装。主90本448,230呼出し一致。公開I/Oから対照・変換54条件すべてを各n回の問い合わせで等価実装へ回復し、主特許候補には不採用。[実測・再現](results/invention-20261023/mutation-quotient-report-v1/report.md)。独立した有力な新規性の確立は引き続き未達。'
if notice not in text:
    first,rest=text.split('\n',1);f.write_text(first+'\n\n'+notice+'\n'+rest,encoding='utf-8')
f=ROOT/'research/novelty-status-20261023.md';text=f.read_text(encoding='utf-8').replace('14%使用（約86%残）','16%使用（約84%残）')
if marker not in text:text+='\n'+marker+'\n\n'+entries['research/novelty-analysis.md']+'\n'
f.write_text(text,encoding='utf-8')
print('Updated 10 research entry points; existing paper/main.tex and paper/README.md untouched.')
