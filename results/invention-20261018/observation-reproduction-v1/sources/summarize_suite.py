"""Regenerate tables from raw data, check denominators, and archive analysis code."""
import argparse, csv, hashlib, json, math, shutil, statistics as st
from pathlib import Path

def stats(xs):
    q=st.quantiles(xs,n=4,method='inclusive')
    return {'median':st.median(xs),'q1':q[0],'q3':q[2],'min':min(xs),'max':max(xs)}

def run(d):
    if (d/'summary.json').exists():raise ValueError('Refuse overwrite')
    read=lambda f:json.loads((d/f).read_text(encoding='utf-8'))
    manifest,plan,runtime=read('manifest.json'),read('plan.json'),read('runtime.json')
    runmap={r['id']:r for r in runtime['rows']};attacks={r['id']:r for r in read('attacks.json')['results']}
    symbolic={r['id']:r for r in read('symbolic.json')['rows']};mem={r['id']:r for r in read('memory.json')['result']}
    transforms=read('transform-resources-sequential/results.json')
    cross=read('cross-engine/results.json');rows=[];timed=False;compile_during=[];blocks=[]
    for line in (d/'runtime.log').read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('TIMING-BEGIN'):assert not timed;timed=True;blocks.append(line)
        elif line.startswith('TIMING-END'):assert timed;timed=False
        elif timed and 'Compiled function' in line:compile_during.append(line)
    assert not timed and len(blocks)==5 and not compile_during
    for a in manifest['artifacts']:
        r=runmap[a['id']];base=runmap[a['program']+'/plain-'+a['level']]
        assert r['checks']==728 and not (r['runMismatches']+r['probeMismatches']+r['memoryMismatches'])
        assert len(r['nsPerCall'])==15 and all(x>0 for x in r['nsPerCall'])
        baseline=next(b for b in manifest['artifacts'] if b['id']==base['id'])
        assert hashlib.sha256((d/a['file']).read_bytes()).hexdigest()==a['sha256']
        row={'id':a['id'],'program':a['program'],'mode':a['mode'],'level':a['level'],'bytes':a['bytes'],
          'size_ratio':a['bytes']/baseline['bytes'],'ns_per_call':stats(r['nsPerCall']),
          'paired_runtime_ratio':stats([x/y for x,y in zip(r['nsPerCall'],base['nsPerCall'])]),
          'recovery_status':symbolic[a['id']]['recovery']['status'],'recovery_ops':attacks[a['id']].get('cost'),
          'attack_ms':attacks[a['id']]['milliseconds'],'linear_memory_bytes':r['memoryBytes'],
          'runtime_process_peak_kib':mem[a['id']]['resourceUsage']['maxRSS'],
          'canonical_seconds':symbolic[a['id']]['canonical']['seconds']}
        trials=[x for x in transforms if x['id']==a['program']+'/'+a['mode']+'-raw']
        row['transform_seconds']=stats([x['seconds'] for x in trials]) if trials else None
        row['transform_parent_peak_bytes']=stats([x['after']['peakWorkingSetBytes'] for x in trials]) if trials else None
        rows.append(row)
    summary={'variants':len(rows),'correctness_per_export':sum(r['checks'] for r in runtime['rows']),
      'correctness_export_calls':3*sum(r['checks'] for r in runtime['rows']),
      'trap_cases':sum(r['traps'] for r in runtime['rows']),'mismatches':0,
      'cross_engine_cases':sum(r['checks'] for r in cross['rows']),
      'cross_engine_mismatches':sum(len(r['mismatches']) for r in cross['rows']),
      'targets_recovered':sum(r['recovery_status']=='proved' for r in rows),'no_target':sum(r['recovery_status']=='no_target' for r in rows),
      'output_expressions_proved':sum(x['output']['status']=='proved' for x in symbolic.values()),
      'normalized_outputs':sum(x['canonical']['status']=='normalized' for x in symbolic.values()),
      'compilation_messages_during_timing':len(compile_during),'rows':rows}
    (d/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    columns=['id','bytes','size_ratio','runtime_median_ns','runtime_q1_ns','runtime_q3_ns','paired_ratio_median','recovery_ops','recovery_status','linear_memory_bytes','runtime_process_peak_kib','attack_ms','transform_median_seconds']
    with (d/'comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for r in rows:w.writerow({'id':r['id'],'bytes':r['bytes'],'size_ratio':r['size_ratio'],
          'runtime_median_ns':r['ns_per_call']['median'],'runtime_q1_ns':r['ns_per_call']['q1'],'runtime_q3_ns':r['ns_per_call']['q3'],
          'paired_ratio_median':r['paired_runtime_ratio']['median'],'recovery_ops':r['recovery_ops'],'recovery_status':r['recovery_status'],
          'linear_memory_bytes':r['linear_memory_bytes'],'runtime_process_peak_kib':r['runtime_process_peak_kib'],'attack_ms':r['attack_ms'],
          'transform_median_seconds':r['transform_seconds']['median'] if r['transform_seconds'] else ''})
    lines=['# 実測比較（自動生成）','','全75条件はcomparison.csvとsummary.json。以下はO3。時間はWasm内batchの1反復あたりで、ホスト呼出し時間ではない。中央値[Q1,Q3]、15反復。倍率はblockごとのplainとの比の中央値。','','|カーネル|方式|bytes|ns/反復 [Q1,Q3]|時間倍率|復元演算数|','|---|---|---:|---|---:|---:|']
    for r in rows:
        if r['level']!='O3':continue
        s=r['ns_per_call'];c=r['recovery_ops'] if r['recovery_ops'] is not None else '対象なし'
        lines.append(f"|{r['program']}|{r['mode']}|{r['bytes']}|{s['median']:.3f} [{s['q1']:.3f},{s['q3']:.3f}]|{r['paired_runtime_ratio']['median']:.3f}|{c}|")
    lines+=['','メモリ: 全条件のWasm線形メモリは65,536 bytes。Node全体のpeak working setは起動・コンパイラを含む。モジュール固有の使用量とはみなさない。',
      f"Node peak範囲 {min(r['runtime_process_peak_kib'] for r in rows):,}–{max(r['runtime_process_peak_kib'] for r in rows):,} KiB。",
      '','変換時間は別の60試行（4方式×5カーネル×3反復）。全生値はtransform-resources-sequential/results.json。生成メモリはPython親のみ、WABT子プロセスのpeakは未測定。',
      '','|方式|変換時間中央値の範囲 ms|Python peak範囲 MiB|','|---|---:|---:|']
    for mode in ('output-only','random','frontier','mba'):
        rr=[r for r in rows if r['mode']==mode and r['level']=='raw'];tt=[r['transform_seconds']['median']*1000 for r in rr]
        peaks=[v['after']['peakWorkingSetBytes']/2**20 for v in transforms if '/'+mode+'-' in v['id']]
        lines.append(f'|{mode}|{min(tt):.2f}–{max(tt):.2f}|{min(peaks):.2f}–{max(peaks):.2f}|')
    (d/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sd=d/'analysis-sources';sd.mkdir()
    for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,sd/p.name)
    for p in Path(__file__).parent.glob('*.cjs'):shutil.copyfile(p,sd/p.name)
    (d/'inventory.json').write_text(json.dumps({str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob('*')) if p.is_file() and p.name!='inventory.json'},indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);run(ap.parse_args().directory)
