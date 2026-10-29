import hashlib,json,pathlib,shutil,statistics,sys
import prototype as p
main,runtime,audit,extra,out=map(lambda x:pathlib.Path(x).resolve(),sys.argv[1:6]);out.mkdir(parents=True,exist_ok=False)
load=lambda root,name:json.loads((root/name).read_text(encoding='utf-8'))
manifest=load(main,'manifest.json');checks=load(main,'checks.json');rs=load(runtime,'summary.json');ats=load(audit,'analysis-timings.json')
assert len(manifest)==70 and checks['calls']==92230 and checks['mismatches']==0
assert len(load(main,'recovery.json'))==14 and len(load(audit,'pruned-recovery.json'))==14
assert len(load(audit,'replay.json'))==56 and all(r['byte_identical'] for r in load(audit,'replay.json'))
assert sum(len(r['inputs']) for r in load(audit,'interpreter.json'))==210
assert len(load(audit,'rejections.json'))==4 and len(load(audit,'negative.json'))==3
assert load(extra,'arithmetic.json')['cases']==4312
for r in manifest:assert p.q.digest(r['file'])==r['sha256']
analysis=[]
for name in ('n8','n32','n128','full32'):
    for mode in ('array','poly','poly-pruned'):
        xs=[r for r in ats if r['name']==name and r['mode']==mode]
        analysis.append(dict(name=name,mode=mode,processes=len(xs),
         read_ms=statistics.median(r['read_ms'] for r in xs),
         body_ms=statistics.median(r['factor_and_evaluate_ms'] for r in xs),
         total_ms=statistics.median(r['analysis_ms'] for r in xs),
         min_total_ms=min(r['analysis_ms'] for r in xs),max_total_ms=max(r['analysis_ms'] for r in xs)))
lines=['# 多項式lookupの実測比較','',
 '時間は3 fresh processの各9 batch中央値の中央値。範囲はprocess中央値の最小–最大。信頼区間ではない。',
 '単位ns/query。共通Wasm loop、入力読取、checksumを含む。単独JS呼出しの時間ではない。','',
 '|対象|方式|hit ns|範囲|miss ns|範囲|binary bytes|','|---|---|---:|---|---:|---|---:|']
for name in ('n8','n32','n128','full32'):
    for mode in ('list','array','poly','poly-pruned'):
        h=next(r for r in rs if (r['name'],r['mode'],r['kind'])==(name,mode,'hit'))
        m=next(r for r in rs if (r['name'],r['mode'],r['kind'])==(name,mode,'miss'))
        lines.append(f'|{name}|{mode}|{h["median_ns"]:.3f}|{h["min_ns"]:.3f}–{h["max_ns"]:.3f}|{m["median_ns"]:.3f}|{m["min_ns"]:.3f}–{m["max_ns"]:.3f}|{h["bytes"]}|')
lines.extend(['','## 既知方式の辞書回復','',
 '3 fresh Python process、公開分割seed 3種類。ms。readerはWABT検証・変換とAST化を含み、Python起動・module importは含まない。',
 '係数抽出・因子分割・補間値評価を本体とし、等価Wasmの再コンパイルは含まない。各欄の中央値を別々に計算するため和は厳密には一致しない。','',
 '|対象|方式|reader ms|本体 ms|合計 ms|合計範囲 ms|','|---|---|---:|---:|---:|---|'])
for a in analysis:lines.append(f'|{a["name"]}|{a["mode"]}|{a["read_ms"]:.3f}|{a["body_ms"]:.3f}|{a["total_ms"]:.3f}|{a["min_total_ms"]:.3f}–{a["max_total_ms"]:.3f}|')
ts=[r['transform']['total_ms'] for r in manifest if r['stage']=='raw' and r['transform']]
rss=[x for r in rs for x in r['rss_kib']]
lines.extend(['',f'全方式の宣言linear memoryは65,536byte。Node全processのpeak RSSは{min(rss)}–{max(rss)}KiB。',
 f'変換・reader・compile・validationを含む変換時間の単発値範囲は{min(ts):.3f}–{max(ts):.3f}ms（全21変換、分布測定ではない）。',
 '高速な対照の一部は校正上限2^18回で5ms未満。CPU affinity/周波数を固定していない。',
 'NotDecの型回復、既存obfuscatorとの同費用比較、人間の解析時間、NTLの速度は測定していない。',
 '実行と解析は別言語・別課題であり、両時間の単純比を安全性指標にしない。'])
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
summary=dict(conditions=70,node_calls=92230,interpreter_probes=210,arithmetic_checks=4312,
 recovered_conditions=28,replayed_binaries=56,rejections=4,negative_witnesses=3,
 runtime_processes=96,analysis_processes=36,analysis=analysis,runtime=rs,
 transform_total_ms_range=[min(ts),max(ts)],peak_process_rss_kib=[min(rss),max(rss)],
 decision='Concrete known-representation experiment; independent novelty unestablished; main invention goal active')
(out/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
snap=out/'sources';snap.mkdir()
sources=list(pathlib.Path(__file__).parent.glob('*.py'))+list(pathlib.Path(__file__).parent.glob('*.cjs'))+list(pathlib.Path(__file__).parent.glob('*.md'))
sources += [p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
for f in sources:shutil.copy2(f,snap/str(f.resolve().relative_to(p.ROOT)).replace('\\','__').replace('/','__'))
pins=[]
for folder in (main,runtime,audit,extra,out):
    for f in sorted(folder.rglob('*')):
        if f.is_file() and f.name!='pins.json':pins.append(dict(file=str(f.relative_to(p.ROOT)),sha256=p.q.digest(f)))
(out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
print(json.dumps(dict(pins=len(pins),**{k:v for k,v in summary.items() if k not in ('analysis','runtime')})))
