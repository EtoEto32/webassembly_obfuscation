# -*- coding: utf-8 -*-
import argparse,json,os,platform,statistics,winreg
from pathlib import Path
import prototype as p
def run(main,runtime,audit,model,output):
    paths=list(map(lambda x:Path(x).resolve(),(main,runtime,audit,model,output)));main,runtime,audit,model,out=paths;out.mkdir(parents=True,exist_ok=False)
    inputs=[main/'manifest.json',main/'checks.json',main/'recovery.json',runtime/'summary.json',runtime/'analysis.json',runtime/'runtime.json',audit/'audit.json',model]
    manifest,checks,recovery,timing,analysis,measurements,aud,mod=[json.loads(x.read_text(encoding='utf-8')) for x in inputs]
    assert checks['positiveCalls']==265680 and checks['positiveMismatches']==0 and checks['unexpectedTraps']==0 and checks['negativeDetected']==6
    positive=[b for b in manifest['binaries'] if not b['negative']];assert len(positive)==36
    assert aud['regenerated']==42 and aud['interpreter_calls']==288 and len(aud['rejections'])==6
    assert len([a for a in recovery if a['status']=='recovered'])==18
    assert len([a for a in recovery if a['mode']=='bad' and a['status']=='unsupported'])==6
    aindex={(r['name'],r['mode'],r['opt']):r for r in analysis};ratios=[]
    for name in ('wide','small','edge'):
        d=aindex[(name,'dynamic','O3')];f=aindex[(name,'fixed','O3')]
        ratios.append(dict(name=name,summary_ratio=d['summary_median_ms']/f['summary_median_ms'],read_plus_summary_ratio=(d['read_median_ms']+d['summary_median_ms'])/(f['read_median_ms']+f['summary_median_ms'])))
    cpu=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
    environment=dict(cpu=winreg.QueryValueEx(cpu,'ProcessorNameString')[0].strip(),logical_processors=os.cpu_count(),platform=platform.platform(),note='Read after benchmark; no affinity/frequency control or isolated stack measurement')
    winreg.CloseKey(cpu)
    summary=dict(positive_conditions=len(positive),positive_calls=checks['positiveCalls'],unique_inputs=checks['uniqueInputs'],negative_conditions=6,adaptive_successes=18,protected_adaptive_successes=12,dynamic_adaptive_successes=6,analysis_ratios=ratios,
        runtime_dynamic_plain_range=[min(r['modes']['dynamic']['median']/r['modes']['plain']['median'] for r in timing['rows']),max(r['modes']['dynamic']['median']/r['modes']['plain']['median'] for r in timing['rows'])],
        runtime_dynamic_fixed_range=[min(r['modes']['dynamic']['median']/r['modes']['fixed']['median'] for r in timing['rows']),max(r['modes']['dynamic']['median']/r['modes']['fixed']['median'] for r in timing['rows'])],
        processes=len(measurements),batches=sum(len(r['measurement']['batches']) for r in measurements),short_batches=timing['short_batches'],max_rss_range_kib=[min(r['measurement']['maxRssKiB'] for r in measurements),max(r['measurement']['maxRssKiB'] for r in measurements)],environment=environment)
    text=['# 再帰frame混合：実測比較','', '各値は保存JSONから生成。実行時間はns/run、3 fresh process中央値の中央値。括弧内はprocess中央値の最小–最大。','', '|設定|深さ|plain|固定混合|動的混合|回復|動的/plain|動的/固定|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in timing['rows']:
        m=r['modes'];cells=[f"{m[v]['median']:.2f} ({m[v]['range'][0]:.2f}–{m[v]['range'][1]:.2f})" for v in ('plain','fixed','dynamic','recovered')]
        text.append('|'+str(r['name'])+'|'+str(r['depth'])+'|'+'|'.join(cells)+f"|{m['dynamic']['median']/m['plain']['median']:.3f}|{m['dynamic']['median']/m['fixed']['median']:.3f}|")
    text+=['','|O3 core bytes|plain|固定|動的|回復|','|---|---:|---:|---:|---:|']
    for name in ('wide','small','edge'):
        d={r['mode']:r['bytes'] for r in timing['binaries'] if r['name']==name};text.append('|'+name+'|'+'|'.join(str(d[m]) for m in ('plain','fixed','dynamic','recovered'))+'|')
    text+=['','解析のvalidate/読取と要約本体を分離。各binary11反復の中央値、コンパイルは含まない。11回は同一Python processで、独立環境11種類ではない。','', '|設定|方式|raw 読取ms|raw 要約ms|O3 読取ms|O3 要約ms|','|---|---|---:|---:|---:|---:|']
    for name in ('wide','small','edge'):
        for mode in ('plain','fixed','dynamic'):
            r=aindex[(name,mode,'raw')];o=aindex[(name,mode,'O3')];text.append(f"|{name}|{mode}|{r['read_median_ms']:.3f}|{r['summary_median_ms']:.3f}|{o['read_median_ms']:.3f}|{o['summary_median_ms']:.3f}|")
    text+=['',f"72 process・648 batch、10ms未満のbatchは{timing['short_batches']}。全例linear memory 0。Node maxRSSは{summary['max_rss_range_kib'][0]}–{summary['max_rss_range_kib'][1]}KiB。JIT・runtimeを含み、Wasm stack単独値ではない。",'', '要約数は全条件1、呼出し履歴の展開数0。動的版の多項式最大項数は29。通常O3後も変換側workerは7引数を持つ。解析本体の小幅増加は保存するが、呼出し文脈数に応じた困難化は支持されない。']
    (out/'comparison.md').write_text('\n'.join(text)+'\n',encoding='utf-8');p.save(out/'summary.json',summary)
    p.save(out/'input-pins.json',{str(x.relative_to(p.ROOT)):p.digest(x) for x in inputs})
    print(json.dumps(summary))
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for k in ('main','runtime','audit','model','output'):ap.add_argument(k)
    a=ap.parse_args();run(a.main,a.runtime,a.audit,a.model,a.output)
