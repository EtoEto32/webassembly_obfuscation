import argparse, json, shutil
from pathlib import Path
from run import q,HERE,p

def main(main,extra,runtime,audit,dst):
    main,extra,runtime,audit,dst=[Path(x).resolve() for x in (main,extra,runtime,audit,dst)];dst.mkdir(parents=True,exist_ok=False)
    a=json.loads((main/'checks.json').read_text());b=json.loads((extra/'checks.json').read_text());r=json.loads((runtime/'summary.json').read_text());atk=json.loads((audit/'recovery.json').read_text());interp=json.loads((audit/'interpreter.json').read_text());replay=json.loads((audit/'replay.json').read_text())
    assert a['positiveMismatches']==b['positiveMismatches']==0
    assert (a['positiveTargets'],b['positiveTargets'],a['negativeWithWitness'])==(24,6,8)
    assert len(atk)==12 and all(x['match'] for x in atk)
    assert len(replay)==6 and all(x['match'] for x in replay)
    assert sum(x['observations'] for x in interp)==70
    rows=r['rows'];lookup={(x['mode'],x['offset']):x for x in rows}
    ratios=[]
    for off in (0,13):
        val=lambda mode:lookup[(mode,off)]['median_ns']
        ratios.append(dict(offset=off,byte_over_block=val('byte')/val('block'),block_over_plain=val('block')/val('plain'),block_over_high=val('block')/val('block-high')))
    summary=dict(positive_conditions=30,positive_call_comparisons=a['positiveCalls']+b['positiveCalls'],positive_expected_traps=a['positiveExpectedTraps']+b['positiveExpectedTraps'],mismatches=0,negative_conditions=a['negativeTargets'],negative_with_witness=8,interpreter_observations=70,byte_replays=6,full_memory_recoveries=12,ratios=ratios,runtime=rows)
    q.save(dst/'report.json',summary)
    lines=['# ページ内block表現の実測比較','','各3 fresh processの7batch中央値をまとめた値。rangeはprocess中央値の最小–最大。独立benchmarkではなく単一合成APIの位置違い。','','|mode|offset|ns/iteration median [min,max]|bytes|linear bytes|process maxRSS median KiB|','|---|---:|---:|---:|---:|---:|']
    for x in rows:lines.append(f"|{x['mode']}|{x['offset']}|{x['median_ns']:.4f} [{x['min_ns']:.4f}, {x['max_ns']:.4f}]|{x['bytes']}|{x['linear_memory_bytes']}|{x['maxRSS_KiB']}|")
    lines+=['','時刻、実行器、batch、calibration、checksumの生値はruntimeディレクトリ参照。単独関数呼出し時間、専用codecメモリ使用量、攻撃開発時間ではない。','','この比較だけでは難読化性能の優位や新規性を示せない。高アドレス優先はMozillaの既知規則による対照で、Firefox JITを直接測定した値ではない。']
    (dst/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sources=[f for f in HERE.iterdir() if f.suffix in ('.py','.cjs','.md')]
    sources += [p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
    pins=[];snap=dst/'sources';snap.mkdir()
    for f in sources:
        name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snap/name)
        pins.append(dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)))
    for folder in (main,extra,runtime,audit):
        for f in sorted(folder.rglob('*')):
            if f.is_file():pins.append(dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)))
    for f in [p.ROOT/'.tools/wabt-1.0.42/bin'/x for x in ('wat2wasm.exe','wasm2wat.exe','wasm-validate.exe','wasm-interp.exe')]+[p.ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe']:
        pins.append(dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)))
    q.save(dst/'pins.json',pins);print(json.dumps(dict(pins=len(pins),summary=summary)))
if __name__=='__main__':
    ap=argparse.ArgumentParser();[ap.add_argument(x) for x in ('main','extra','runtime','audit','output')];a=ap.parse_args();main(a.main,a.extra,a.runtime,a.audit,a.output)
