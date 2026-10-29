# -*- coding: utf-8 -*-
import ast, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
marker='observer-closure/README.md'
paragraph='''[有限精度の観測閉包](research/observer-closure/README.md)を自動生成し、実Wasmへ実装した。主30正条件780,090 API呼出しは一致したが、全12変換を10step観測で小さな更新へ回復。reset/peekを削った追試でも全12変換を22stepで回復し、491,520stepは一致した。実行費用は元の約5.18–10.05倍で、既知の観測実現・多項式持上げを超える新規性と保護優位は未確立。主特許候補には不採用。[実測と再現](results/invention-20261023/observer-closure-report-v1/report.md)。'''
readme=ROOT/'README.md';text=readme.read_text(encoding='utf-8')
if marker not in text:
    first,rest=text.split('\n',1);readme.write_text(first+'\n\n2026-10-23追補：'+paragraph+'\n'+rest,encoding='utf-8')
notes={
 'experiments.md':'3人工kernel、raw/O3、full/quotient、正当性を破るbad対照を比較。小幅42閉包524,256状態入力対、主12+追試12の関数係数証明、WABT360step・90最終観測、36process252batchを保存。回復器のcandidate出力と別途の証明を区別する。',
 'literature-review.md':'Sontagの2026年プレプリント（1976年博士論文の更新）、Iacob/Schoukens/TóthのIFAC2023有限Koopman構成、BruntonほかPLoS ONE2016、WO2013142979A1の関連箇所を実際に閲覧。[書誌・既読範囲・技術差](observer-closure/prior-art.md)。',
 'candidates.md':'過去の線形torsion-state、手選択のsymmetric-stateと違い、非線形更新から単項式と必要なbit精度をworklistで生成した。ただし自動閉包・精度変更・API削除を独立した発明数へ数えない。原理の先行性と容易な回復が最大のReject理由。',
 'research-gap.md':'可逆表現を避けても、出力の選択入力差分から更新の合同類が出れば同等コードを安く構築できる。resetを消すだけでは、新instanceと入力制御によるstate設定を防げなかった。次の候補はこの反証を避ける具体的生成規則と費用根拠を先に必要とし、非一意性だけから保護を推定しない。',
 'novelty-analysis.md':'有限環の係数消滅を使った具体worklistは保存したが、Koopman/Carleman、observable realization、有限環多項式の既知枠組みとの差だけで特許性を断定しない。先行特許の請求項1は入力依存M-register配置であり、本案と同一と認定したわけでもない。',
 'threat-model.md':'方式既知、任意実行・新instance作成が可能、次数上限4とAPI仕様が公開。攻撃には元F・内部global・変換係数を渡さず、export経由の入出力だけを使った。reset不可の追試は公開APIを揃えて比較する別profileで、元の3export APIを完全保存する変換と混同しない。',
 'algorithm.md':'[閉包の疑似コードと証明](observer-closure/algorithm.md)。z_j=2^e_j x^jを用い、(F(X)+U)^jの係数の2進付値から必要精度を反復生成。形式係数の条件内の閉包であり、関数として最小のstateやmemoryを生成するとの主張はしない。',
 'novelty-status-20261023.md':'主発明の確立は未達。生成器・実験・失敗原因を保存した進捗であり、研究全体は完了扱いしない。直近の取得可能な週枠は34%使用・66%残。正確なtoken残高は取得できず、残り20%には到達していない。'}
for name,extra in notes.items():
    f=ROOT/'research'/name;old=f.read_text(encoding='utf-8')
    if marker not in old:
        para=paragraph.replace('(research/','(').replace('(results/','(../results/')
        f.write_text(old+'\n\n## 有限精度の観測閉包と選択入力回復（2026-10-23）\n\n'+para+'\n\n'+extra+'\n',encoding='utf-8')
f=ROOT/'paper-draft.md';old=f.read_text(encoding='utf-8')
if marker not in old:
    f.write_text(old+'\n\n## 追加評価：有限精度の観測閉包（2026-10-23）\n\n'+paragraph+'''\n\n元の状態を非単射な観測関数群へ置換する方式を検査した。出力x²から出発し、次状態F(x)+uの持上げに必要な単項式と精度を係数の2進付値で閉じる。各座標の更新を同時に行うことで意味を保存する。3例で5–6wordの閉包が生成され、小幅の全列挙と実Wasmの連続API試験で一致した。\n\n方式既知の解析者は、reset(s)後の入力0と1に対する二乗出力の差から2F(s)を得る。5点の有限環補間によりF mod2^31を回復すれば、元と同等の出力列を持つ1word更新を構成できる。元のxそのものの一意復号は不要である。resetとpeekを除いても、新instanceへの最初の入力で同じ合同類を設定でき、22stepの攻撃が成立した。\n\nfull対照に対するquotientの時間差は小さく測定ばらつきが重なる。一方、元に対する約5.18–10.05倍の費用にもかかわらず、少数観測で回復できた。自動閉包という実装上の相違を、既存の観測実現・多項式持上げから独立した新規性や有効な保護と同一視しない。今回の否定結果は加算入力・二乗出力・低次数profileに限定され、非単射状態変換一般の不可能性ではない。\n''',encoding='utf-8')

pins=json.loads((ROOT/'results/invention-20261023/observer-closure-report-v1/sha256.json').read_text(encoding='utf-8'))
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
mismatch=[name for name,value in pins.items() if digest(ROOT/name)!=value]
assert not mismatch,mismatch
pyfiles=list((ROOT/'research/observer-closure').glob('*.py'))+[Path(__file__)]
for f in pyfiles:ast.parse(f.read_text(encoding='utf-8'))
jsfiles=list((ROOT/'research/observer-closure').glob('*.cjs'))
for f in jsfiles:
    r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stderr
links=[]
for f in (ROOT/'research/observer-closure').glob('*.md'):
    for ref in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if ref.startswith(('https://','http://','#')):continue
        target=(f.parent/ref.split('#')[0]).resolve();assert target.exists(),(f,ref);links.append(ref)
paper_hashes={'paper/main.tex':'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225','paper/README.md':'10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
assert all(digest(ROOT/f)==v for f,v in paper_hashes.items())
verification={'hashes_verified':len(pins),'mismatches':mismatch,'python_ast':len(pyfiles),'node_syntax':len(jsfiles),'local_links':len(links),'unrelated_paper_hashes':paper_hashes,'weekly_used_percent':34,'weekly_remaining_percent':66,'goal_completed':False}
(ROOT/'results/invention-20261023/observer-closure-verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification))
