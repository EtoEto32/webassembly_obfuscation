"""Complete archival after the relative/absolute pin-path development error.

Does not repeat or invent checks; checks already-saved successful results.
"""
import hashlib
import json
from pathlib import Path
import sys
import prototype as p

def main(folder):
    folder=Path(folder).resolve()
    if (folder/'experiment.json').exists():
        r=json.loads((folder/'experiment.json').read_text())
        assert len(r['attacks'])==36
        correctness=json.loads((folder/'check.stdout.log').read_text())
        assert correctness['mismatches']==0 and correctness['total_calls']>0
        assert not (folder/'check.stderr.log').read_text()
        r['correctness']=correctness
        (folder/'experiment.json').write_text(json.dumps(r,indent=2),encoding='utf8')
    else:
        r=json.loads((folder/'audit.json').read_text());assert r['scratch']['mismatches']==0
        assert len(r['forged_rejections'])==9 and r['exact_raw_O3_kernel_checks']==18
    (folder/'archival-note.md').write_text('検査後のhash一覧保存で相対pathと絶対pathの混在を検出して停止した。検査失敗ではない。finalize.pyが既存の成功ログを確認し、hash一覧保存を完了した。検査の追加実行数には算入しない。\n',encoding='utf8')
    pins={str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.rglob('*') if f.is_file() and f.name!='pins.json'}
    (folder/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8');print(json.dumps({'files_pinned':len(pins),'folder':str(folder)}))

if __name__=='__main__':main(sys.argv[1])
