# -*- coding: utf-8 -*-
import ast,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];marker='synchronizing-decoder/README.md'
para='''[重みを伴う解釈状態の同期](research/synchronizing-decoder/README.md)を実Wasmへ実装し、主54条件62,208呼出しと代表回復12条件13,824呼出しの一致を確認した。非可逆遷移で全入口を同じ計算へ収束できたが、代表状態一つで全12sync条件を全状態解析とbyte一致のコードへ回復。元の約3.71–30.80倍の実行費用に対して追加保護の根拠が弱く、weighted synchronizationにも先行性があるため主案に不採用。[実測と再現](results/invention-20261023/synchronizing-decoder-report-v1/report.md)。'''
f=ROOT/'README.md';old=f.read_text(encoding='utf-8')
if marker not in old:
    first,rest=old.split('\n',1);f.write_text(first+'\n\n2026-10-23追補：'+para+'\n'+rest,encoding='utf-8')
notes={
 'literature-review.md':'Iván, Synchronizing weighted automata（AFL 2014）の定義と、Kilger/Auer/Andreas, VMSpec（2026-10-21 preprint）のVM context・handler要約・限界を実読。[書誌と既読範囲](synchronizing-decoder/prior-art.md)。著者の評価と本研究で実行したツールを区別する。',
 'research-gap.md':'単射の鍵更新を非可逆な同期に変えると合流の原始操作は作れた。しかし全入口の結果を一致させる保証は、解析者にも代表入口一つを選ぶ理由を与える。検証のための全状態費用を候補生成の必須費用とみなさない。',
 'candidates.md':'同期語の重み生成を新しい実装仮説として検査したが、fixed/syncや状態数4/8を別発明に数えない。一般のweighted synchronizationへ直接対応し、安い代表要約も残ることが最大のReject理由。',
 'threat-model.md':'方式既知、全binaryを読める。回復器は元source・seed・係数manifestを入力にしない。全入口の正確なaffine検査と、同期の約束に依存する代表候補生成を分けた。後者は未知の任意binaryの同値証明ではない。',
 'algorithm.md':'[同期語・係数kernel生成・意味保存](synchronizing-decoder/algorithm.md)。Cerny型の既知同期語の辺訪問行列CについてCα=a1、Cβ=b1をmod2^32で満たす重みを生成。単一加算potentialでは説明できない96例も、語全体のaffine解釈で戻せた。',
 'novelty-analysis.md':'G=(Z/2^32)^2のpowerset semiringへ重みを移せば、状態と係数を同時に同期させる条件はIvánの既知定義と対応する。Wasmへ実装したことやpotential以外の重みがあることだけを独立特許性と同一視しない。',
 'experiments.md':'96gateの係数検査、縮小幅9,216組、WABT324呼出し、24回復のbyte再生成、12誤重み対照、profile外拒否、63process441batchを保存。元のifは維持し、任意CFGの合流を処理するcompilerまでは実装していない。原始操作段階の反証から拡張を見送った。',
 'novelty-status-20261023.md':'主発明は未確立。今回も機能する変換を実装して適応回復を検査した進捗であり、研究全体の完了ではない。直近週枠38%使用・62%残、正確なtoken残数は取得不可。ユーザー指定の残り20%には未到達。'
}
for name,note in notes.items():
    f=ROOT/'research'/name;old=f.read_text(encoding='utf-8')
    if marker not in old:f.write_text(old+'\n\n## 非可逆な解釈状態の同期（2026-10-23）\n\n'+para.replace('(research/','(').replace('(results/','(../results/')+'\n\n'+note+'\n',encoding='utf-8')
f=ROOT/'paper-draft.md';old=f.read_text(encoding='utf-8')
if marker not in old:
    f.write_text(old+'\n\n## 追加評価：重みを伴う解釈状態の同期（2026-10-23）\n\n'+para+'''

非可逆な状態遷移を使うと、可逆更新のみの鍵整合性条件で生じた合流の矛盾を避けられる。本試作はこの原始操作を、全入口状態から同じ算術更新を行う表駆動helperとして構成した。既知の同期語の各辺に係数対を置き、語の辺訪問回数から得た線形制約を満たすように生成する。個々の辺重みは単一の加算potentialに還元できなくても、語全体では正しい更新になる。

ただし、この一般条件はweighted synchronizationの先行定義に対応する。全入口を検証する解析では4/8状態に応じた費用増がある一方、方式既知の解析者は代表入口だけから同等計算の候補を生成できた。その候補は12条件全てで全状態解析の出力とbyte一致した。syncの実行費用は元の約3.71–30.80倍で、代表解析の費用はfixed対照と近かった。従って検証費用の増大を保護効果として主張しない。

実装は元のif構造を維持し、helper入口の解釈状態を引数から作る。任意CFG間で解釈状態を持ち回る変換器までは作っていない。基礎操作に安い要約があるため、その拡張を先に作る根拠は弱いと判断した。今回の否定結果は、この有限状態・affine重みの生成族に限定される。
''',encoding='utf-8')
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pins=json.loads((ROOT/'results/invention-20261023/synchronizing-decoder-report-v1/sha256.json').read_text(encoding='utf-8'))
mismatch=[f for f,h in pins.items() if digest(ROOT/f)!=h];assert not mismatch,mismatch
pyfiles=list((ROOT/'research/synchronizing-decoder').glob('*.py'))+[Path(__file__)]
for f in pyfiles:ast.parse(f.read_text(encoding='utf-8'))
jsfiles=list((ROOT/'research/synchronizing-decoder').glob('*.cjs'))
for f in jsfiles:
    r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stderr
links=[]
for f in (ROOT/'research/synchronizing-decoder').glob('*.md'):
    for ref in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if ref.startswith(('https://','http://','#')):continue
        assert (f.parent/ref.split('#')[0]).resolve().exists(),(f,ref);links.append(ref)
paper_hashes={'paper/main.tex':'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225','paper/README.md':'10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
assert all(digest(ROOT/f)==h for f,h in paper_hashes.items())
v={'hashes_verified':len(pins),'mismatches':mismatch,'python_ast':len(pyfiles),'node_syntax':len(jsfiles),'local_links':len(links),'unrelated_paper_hashes':paper_hashes,'weekly_used_percent':38,'weekly_remaining_percent':62,'goal_completed':False}
(ROOT/'results/invention-20261023/synchronizing-decoder-verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8');print(json.dumps(v))
