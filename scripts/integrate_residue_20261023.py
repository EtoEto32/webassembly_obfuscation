# -*- coding: utf-8 -*-
from pathlib import Path
import json
import hashlib

root = Path(__file__).resolve().parents[1]
title = '剰余表現とWasm整数wrapの成立性ゲート（2026-10-23）'
note = '''[実装・測定](residue-wrap/README.md)。既知RNCの明示した移植規則を検査し、odd版全6条件で誤答、二修正版を含む正24条件101,208呼出しで一致した。aligned版はraw/O3全6条件を元とbyte一致するWasmへ回復。修正版は元の約2.76–15.25倍の実行時間となり、主特許候補には不採用。著者実装のバグ、RNS一般の不可能性、新しい環の定理は主張しない。'''
sections = {
    'research/experiments.md': note+' 別WABT正192・負48・回帰16呼出し、30本byte再現、8拒否対照、縮小幅524,256比較、6補題UNSAT、36process/252batchを保存した。',
    'research/novelty-status-20261023.md': note+' [最も近い先行技術と確認範囲](residue-wrap/prior-art.md)。残高直近確認は週枠27%使用、73%残であり、正確なtoken残高ではない。',
    'research/research-gap.md': '[成立条件](residue-wrap/algorithm.md)。符号化domainの法MがWasmの2^32より大きいだけではword wrapを保存できない。積Mを2^32の倍数へ合わせる修正は、互いに素なmoduliの一成分にword射影を露出させた。正当性を修正したことと新しい保護効果を分ける。',
    'research/candidates.md': note+' 既知RNCの成立性ゲートであり、原理の異なる新発明候補数には加算しない。',
    'research/threat-model.md': '[今回の射影器](residue-wrap/algorithm.md)は公開binaryだけを読み、純粋な全域整数演算をmod2^32へ抽象化する。原source・seed・manifest不要。opaque remの内部のlocal.teeは追跡し、副作用・trap可能演算は値が消えても拒否。未対応を耐性に数えない。対象は単一2引数式で、memory・分岐・一般関数は未評価。',
    'research/literature-review.md': '[RNCと有限語長意味論の追補](residue-wrap/prior-art.md)。Demissie/Ceccato/TiellaのSPRO2015著者論文、PhatakのRNS公開特許、Spielmann/Kuncakのtransducer構成について読んだ範囲を明記。RNC原理とdecode/operate/encodeは既知であり、今回の反例を先行著者実装へ帰属しない。',
    'research/novelty-analysis.md': note,
    'paper-draft.md': note.replace('(residue-wrap/', '(research/residue-wrap/')+' 成立性の否定結果として追補し、主提案の独立した新規性や特許性を得たという主張へ追加しない。',
}
for filename, text in sections.items():
    file = root/filename; old = file.read_text(encoding='utf-8')
    if title in old: raise RuntimeError('already integrated '+filename)
    file.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text+'\n', encoding='utf-8')
file = root/'README.md'; old = file.read_text(encoding='utf-8')
entry = '2026-10-23追補：'+note.replace('(residue-wrap/', '(research/residue-wrap/')+' [集計](results/invention-20261023/residue-wrap-report-v2/report.md)。'
file.write_text(old.replace('\n\n','\n\n'+entry+'\n\n',1), encoding='utf-8')
pins = []
for name in ('residue-wrap-v2','residue-wrap-model-v1','residue-wrap-runtime-v1','residue-wrap-audit-v1','residue-wrap-report-v2'):
    folder = root/'results/invention-20261023'/name
    for e in json.loads((folder/'provenance.json').read_text(encoding='utf-8')):
        digest = hashlib.sha256((folder/e['file']).read_bytes()).hexdigest()
        if digest != e['sha256']: raise AssertionError((name,e['file']))
        pins.append((name,e['file']))
verification = dict(verified_hashes=len(pins), mismatch=0, account_weekly_used_percent=27, account_weekly_remaining_percent=73,
                    cpu_note='CPU identity in README inherited from earlier experiment records; fresh CIM query unavailable.',
                    untouched_user_files=['paper/main.tex','paper/README.md'])
(root/'results/invention-20261023/residue-wrap-verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification))
