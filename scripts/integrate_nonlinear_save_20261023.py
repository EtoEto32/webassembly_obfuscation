# -*- coding: utf-8 -*-
"""Integrate bounded findings without editing the separately maintained TeX paper."""
import ast, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
marker='nonlinear-save/README.md'
paragraph='''[非線形共有退避](research/nonlinear-save/README.md)を実Wasmへ実装した。探索600例中1例と独立holdout600例中1例で、最良線形保存2bitに対して1bitを達成。主42条件40,362呼出しと追試14条件12,614呼出しは一致した。ただし公開APIから全24変換条件を同等遷移表へ回復でき、既知のfunctional index coding・cographとの差も弱い。表生成の補助的最適化として保存し、主たる難読化発明には不採用。[実測と再現](results/invention-20261023/nonlinear-save-report-v1/report.md)。'''
readme=ROOT/'README.md';old=readme.read_text(encoding='utf-8')
if marker not in old:
    first,rest=old.split('\n',1);readme.write_text(first+'\n\n2026-10-23追補：'+paragraph+'\n'+rest,encoding='utf-8')
notes={
 'literature-review.md':'Gupta/Rajanのfunctional index codingの定義・命題1–2・Algorithm 1を実読し、今回の副情報/要求関数の条件と直接対応することを確認。LDT graphのcograph性も既知。[書誌・既読範囲](nonlinear-save/prior-art.md)。',
 'research-gap.md':'既存side-saveの線形入口保存では非線形表現に対し余分なbitが必要な場合がある。ただし非線形彩色への置換は既知の符号化枠組みで説明でき、保存情報の削減だけでは解析耐性を補えない。',
 'candidates.md':'彩色保存・線形保存・全保存は同じrepair方式の比較要素であり、別原理の発明3案とは数えない。最大のReject理由は一般の符号化とcograph分解の適用に見えること、16状態profileで安く回復できること。',
 'threat-model.md':'方式と4bit profileを公開し、全入力実行を許す。回復器には元encoding・copy列・manifestを渡さない。reset/run/peekによる学習は2copyで150、3copyで200 API呼出し。回復は同等動作であり元ソースの一意復元ではない。',
 'algorithm.md':'[二つの情報損失階層からのunion/join彩色](nonlinear-save/algorithm.md)。色数とclique下界を一致させて最小の固定長入口情報を得る。最小CPU local数、実メモリ、実行時間を保証するものではない。',
 'novelty-analysis.md':'独立holdoutの1例でもbit削減が再現したが、機能符号化の一般条件やcograph性は既知。Wasm copyのtrap修復へ落とす生成器という技術差は保存し、特許性は未確立とする。',
 'experiments.md':'全8!の3bit置換40,320例は線形に対するbit削減0。主・holdoutの正条件56件は一致、負対照8件は反例あり。WABT420run・294期待trap、性能45process315batch。改善主例のrepair表192→96byte、O3 binary649→606byteだが、saved i32 local一つ・1page memoryは変わらず。',
 'novelty-status-20261023.md':'主発明の確立は未達。動く生成器と限定的な表削減は得たが、保護効果の向上は支持されない。直近週枠は36%使用・64%残。正確なtoken残高は取得できず、残り20%には未到達。研究全体を完了扱いしない。'
}
for name,extra in notes.items():
    f=ROOT/'research'/name;old=f.read_text(encoding='utf-8')
    if marker not in old:
        para=paragraph.replace('(research/','(').replace('(results/','(../results/')
        f.write_text(old+'\n\n## 非線形共有退避の生成と限界（2026-10-23）\n\n'+para+'\n\n'+extra+'\n',encoding='utf-8')
f=ROOT/'paper-draft.md';old=f.read_text(encoding='utf-8')
if marker not in old:
    f.write_text(old+'\n\n## 追加評価：非線形表現の共有退避（2026-10-23）\n\n'+paragraph+'''

非線形に表現したメモリにcopy列をそのまま適用し、正常終了または失敗prefixで表現を修復する問題を検討した。入口で保存すべき情報は、現物理状態が等しいのに修復先が異なる入口対を分離するcodeである。現状態と修復先の同値類がともに併合のみを行うため、二つの階層を比較したグラフはunion/joinで分解できる。彩色と同じ大きさのcliqueを生成し、この有限領域で最小の保存alphabetを検証した。

この定式化はfunctional index codingに包含され、時刻比較によるcographの原理にも先行研究がある。今回実装したのは限定Wasm profileからの生成と、trap後の再呼出しまで含む意味保存である。これを一般符号化の新定理とは主張しない。探索例と分離したholdoutの双方で稀なbit削減例を確認したが、実際のsaved localとmemory page数は変わらない。

全24変換条件は150–200回の公開API呼出しから同等遷移表に回復できた。主改善例のO3バイナリは最良線形保存649byteから606byteに減った一方、実行時間の明確な改善はなかった。この結果は非線形の保存codeを生成する補助技術の実装可能性を支持するが、従来方式を上回る解析耐性や独立した特許性を支持しない。
''',encoding='utf-8')
pins=json.loads((ROOT/'results/invention-20261023/nonlinear-save-report-v1/sha256.json').read_text(encoding='utf-8'))
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
mismatch=[name for name,value in pins.items() if digest(ROOT/name)!=value];assert not mismatch,mismatch
pyfiles=list((ROOT/'research/nonlinear-save').glob('*.py'))+[Path(__file__)]
for f in pyfiles:ast.parse(f.read_text(encoding='utf-8'))
jsfiles=list((ROOT/'research/nonlinear-save').glob('*.cjs'))
for f in jsfiles:
    r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stderr
links=[]
for f in (ROOT/'research/nonlinear-save').glob('*.md'):
    for ref in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if ref.startswith(('https://','http://','#')):continue
        target=(f.parent/ref.split('#')[0]).resolve();assert target.exists(),(f,ref);links.append(ref)
paper_hashes={'paper/main.tex':'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225','paper/README.md':'10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
assert all(digest(ROOT/f)==v for f,v in paper_hashes.items())
v={'hashes_verified':len(pins),'mismatches':mismatch,'python_ast':len(pyfiles),'node_syntax':len(jsfiles),'local_links':len(links),'unrelated_paper_hashes':paper_hashes,'weekly_used_percent':36,'weekly_remaining_percent':64,'goal_completed':False}
(ROOT/'results/invention-20261023/nonlinear-save-verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8');print(json.dumps(v))
