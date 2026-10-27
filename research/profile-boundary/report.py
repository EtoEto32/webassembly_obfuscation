# -*- coding: utf-8 -*-
import ast
import json
from pathlib import Path
import statistics
import sys
import recover as r


def main(main_dir,adapt_dir,audit_dir,holdout_dir,dest):
    dirs=list(map(lambda s:Path(s).resolve(),(main_dir,adapt_dir,audit_dir,holdout_dir)))
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
    hashes=0
    for folder in dirs:
        for pin in read(folder,'provenance.json'):
            if r.p.q.digest(folder/pin['file'])!=pin['sha256']:raise AssertionError('provenance mismatch')
            hashes+=1
    old=read(dirs[0],'attacks.json');new=read(dirs[1],'attacks.json');extra=read(dirs[3],'outcomes.json')
    checks=[read(dirs[i],'checks.json') for i in (0,1,3)];audit=read(dirs[2],'audit.json')
    summary=dict(old={s:sum(x['status']==s for x in old) for s in ('success','unsupported','timeout','crash')},
                 adapted_success=len(new),extra_success=sum(x['status']=='success' for x in extra),
                 extra_structure_unsupported=sum(x.get('reason')=='unsupported update/observer structure' for x in extra),
                 extra_range_counterexamples=sum(x.get('reason')=='range proof sat' for x in extra),
                 node_calls=sum(x['calls'] for x in checks),node_traps=sum(x['traps'] for x in checks),
                 node_mismatches=sum(x['mismatches'] for x in checks),wabt_calls=audit['interpreter_calls'],
                 wabt_traps=audit['interpreter_traps'],replayed=len(audit['replay']),verified_hashes=hashes,
                 recovery_ms=dict(min=min(x['wall_ms'] for x in new),median=statistics.median(x['wall_ms'] for x in new),max=max(x['wall_ms'] for x in new)))
    r.p.q.save(out/'summary.json',summary)
    text=f'''# 解除器の適用範囲の実測

旧解除器は84条件中24成功、60形式未対応、crash/timeoutは0。範囲証明を含む拡張で84/84を回復し、すべて元のplainとbyte一致した。追加の未知式24条件も回復したが、正しいself-partner12条件はなお形式未対応。範囲不正の12条件はSMT反例により拒否した。

Node正条件の延べ{summary['node_calls']:,}呼出し、期待trap {summary['node_traps']:,}、不一致{summary['node_mismatches']}。同じ6人工fixtureと重複した回復binaryを含む条件数であり、独立プログラム数ではない。WABTは主と拡張回復の{summary['wabt_calls']:,}呼出し、{summary['wabt_traps']}trap。追加式はNodeのみ。主{summary['replayed']}本のbyte再現、計{hashes}hashを検査した。

この結果は新しい難読化発明の成功ではない。式の変更による形式未対応を保護効果へ数えないための評価改善である。拡張解除器も周辺の生成形式照合に依存し、一般的なWasm解析器ではない。

説明・再現は[README](../../../research/profile-boundary/README.md)。各入力directoryのraw JSON、ログ、source snapshotを保存した。実行時間・メモリの新しい保護性能比較は行っていない。
'''
    (out/'report.md').write_text(text,encoding='utf-8')
    snapshot=out/'sources';snapshot.mkdir()
    for f in sorted(r.HERE.glob('*')):
        if f.suffix not in ('.py','.cjs','.md'):continue
        if f.suffix=='.py':ast.parse(f.read_text(encoding='utf-8'))
        (snapshot/f.name).write_bytes(f.read_bytes())
    r.p.q.save(out/'provenance.json',[dict(file=str(f.relative_to(out)),sha256=r.p.q.digest(f)) for f in sorted(out.rglob('*')) if f.is_file()])
    print(json.dumps(summary))


if __name__=='__main__':main(*sys.argv[1:])
