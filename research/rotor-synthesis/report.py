# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import sys
import prototype as p

def main(out):
    base=p.ROOT/'results/invention-20261023';out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    read=lambda folder,file:json.loads((base/('rotor-synthesis-'+folder)/file).read_text(encoding='utf8'))
    runtime=read('native-runtime-v1','summary.json');attacks=read('native-v1','attacks.json');ma=read('main-v1','attacks.json')
    lines=['# 切替グラフ合成：実測と判断','','2026-10-23。既知のrotor計算と有限仕様合成を超える新規性は未確立。実装・検査済みだが、今回の候補は主案に採用しない。研究全体の完了ではない。','','|関数|方式|O3 bytes|実行中央値ns|解析本体ms|','|---|---|---:|---:|---:|']
    for r in runtime['targets']:
        a=next((a for a in attacks if a['name']==r['name'] and a['mode']==r['mode'] and a['optimization']=='O3'),None)
        if r['mode']=='rotor':a=next(a for a in ma if a['name']==r['name'] and a['optimization']=='O3')
        lines.append('|'+ '|'.join([r['name'],r['mode'],str(r['core_bytes']),f'{r["median_ns"]:.4f}',f'{a["analysis_ms"]:.4f}' if a else '対象外'])+'|')
    lines+=['','解析本体は単回診断値で、read/compileを除く。rotorは8入力を全数追跡、native/tightは実命令からのBDD記号実行なので、両者の時間差を保護強度の比と表現しない。共通評価器の別BDD解析も全6条件を回復。','','|検査|呼出し|不一致|','|---|---:|---:|']
    for f,label in [('main-v1','共通評価器、元、回復'),('native-v1','直接命令化、削減、回復'),('audit-v1','共通評価器の別BDD回復')]:
        c=read(f,'correctness.json');assert c['mismatches']==0;lines.append(f'|{label}|{c["calls"]:,}|0|')
    lines+=['','呼出しの入力は重複・方式間再使用を含む。各binary4,833呼出し。48主binaryと6追加回復binary。byte再現18、WABT72呼出し。拒否対照6件。4switchの全体合成は3/3成功、変換は181〜265msでsolver・WABT起動込み単回。xor3の別制約5switch10stepはInt20秒timeout、BitVec14.64秒UNSAT。後者は一般的不可能性を意味しない。','','45fresh process×7batch、全315batch10ms以上。warmup16,384、20ms校正、同一Wasm内loop/入力更新。Node24.15/V8 13.6.233.17-node.48、Windows、i9-11900K、WABT1.0.42、Binaryen133、Python3.9、Z34.13.3。raw.jsonにprocess中央値、RSS、checksum、生batchを保存。tightのlinear memory0、rotor65,536byte。','','読み方・生成規則・意味保存の範囲・先行研究・再現コマンドはresearch/rotor-synthesis/README.mdとprior-art.md。ソースsnapshotは下記sources/。ツールはrepoの.toolsに別途必要。','']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
    for folder in ('rotor-synthesis','connectivity-elimination','span-mask'):
        for src in (p.ROOT/'research'/folder).iterdir():
            if src.is_file() and src.suffix in ('.py','.cjs','.md'):
                dest=out/'sources'/src.relative_to(p.ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    pins={}
    for folder in base.iterdir():
        if folder.is_dir() and folder.name.startswith('rotor-synthesis-'):
            for f in folder.rglob('*'):
                if f.is_file():pins[str(f.relative_to(p.ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    (out/'pins.json').write_text(json.dumps(pins,indent=2))
    for name,h in pins.items():assert hashlib.sha256((p.ROOT/name).read_bytes()).hexdigest()==h
    print(json.dumps({'report':str(out/'report.md'),'pinned_files':len(pins)}))

if __name__=='__main__':main(sys.argv[1])
