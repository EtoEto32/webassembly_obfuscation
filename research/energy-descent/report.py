# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p

def main(main,perf,audit,dst):
    main,perf,audit,root=map(Path,(main,perf,audit,dst));root.mkdir(parents=True,exist_ok=False);pin_counts={}
    for src in (main,perf,audit):
        pins=json.loads((src/'pins.json').read_text())
        for f,h in pins.items():assert hashlib.sha256((src/f).read_bytes()).hexdigest()==h
        pin_counts[src.name]=len(pins)
    m=json.loads((main/'manifest.json').read_text());c=json.loads((main/'checks.json').read_text());b=json.loads((perf/'performance.json').read_text());a=json.loads((audit/'audit.json').read_text())
    r=subprocess.run(['node',str(p.HERE/'verify-performance.cjs'),str(main),str(perf)],capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError(r.stderr)
    verify=json.loads(r.stdout)
    positive=[x for x in c['rows'] if not x['negative']];negative=[x for x in c['rows'] if x['negative']]
    facts={'positive_conditions':len(positive),'positive_calls':sum(x['calls'] for x in positive),'mismatches':sum(x['mismatches'] for x in positive),'traps':sum(x['traps'] for x in positive),'negative_counterexamples':sum(x['mismatches']>0 for x in negative),'negative_calls':sum(x['calls'] for x in negative),'recoveries':len(m['attacks']),
           'byte_replays':len(a['byte_replay']),'wabt_calls':sum(x['calls'] for x in a['wabt']),'local_rule_cases':a['local_rule_cases'],'positive_byte_distinct':len({hashlib.sha256((main/x['file']).read_bytes()).hexdigest() for x in positive}),
           'analysis_total_ms':[min(x['milliseconds'] for x in m['attacks']),max(x['milliseconds'] for x in m['attacks'])],
           'transform_ms':[min(x['milliseconds'] for x in m['transforms']),max(x['milliseconds'] for x in m['transforms'])],
           'rss_KiB':[min(x['maxRSSKiB'] for x in b['rows']),max(x['maxRSSKiB'] for x in b['rows'])],
           'verified_pins':pin_counts,'performance_verification':verify,'performance':b['summary'],'core_timings':a['core_timings'],
           'versions':{tool:p.w.tool(tool,['--version']).strip() for tool in ('wat2wasm','wasm-opt')}}
    lines=['# 違反量による計算の比較','', 'O3。nsは各processの7batch中央値を取り、その3processの中央値。小さいBoolean回路の共通Wasm loop内測定であり、一般アプリの倍率ではない。', '', '| model | mode | bytes | ns/call | process中央値の範囲 | linear memory B |','|---|---|---:|---:|---:|---:|']
    for t in b['summary']:lines.append(f'| {t["name"]} | {t["mode"]} | {t["optimized_bytes"]} | {t["ns"]:.3f} | {t["range_ns"][0]:.3f}–{t["range_ns"][1]:.3f} | {t["linear_memory_bytes"]} |')
    lines+=['','全18保護条件の回復が成功。未対応・クラッシュ・timeoutは主条件で0。回復器は方式専用で、公開係数表と既知の実行器のbyte一致を検査する。原型とO3の再生成を含む総時間は1回測定であり、回復本体の11回測定と混同しない。','',f'正条件 {facts["positive_conditions"]}、呼出し {facts["positive_calls"]}、不一致 {facts["mismatches"]}、予期しないtrap {facts["traps"]}。等重み6条件すべてに誤答あり。', '', '実行費用と近い既存構成から、この案を主発明に採用しない。']
    (root/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf8');(root/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    for file in ('report.py','verify-performance.cjs'):shutil.copyfile(p.HERE/file,root/('source-'+file))
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in facts.items() if k not in ('performance','core_timings','performance_verification')},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
