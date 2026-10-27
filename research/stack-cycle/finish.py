"""Independent-process runtime samples and second-engine wrapper checks."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import time
import transform as t
from experiment import save


def interpreter(out,rows):
    report=[];p=out/'interpreter';p.mkdir(exist_ok=False)
    for row in rows:
        src=out/row['path'];mod=t.w.parse(t.w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names']))
        # Every wrapper instantiation starts with the same module data segment.
        cases={
          'xorshift16':[['(i32.const 0)'],['(i32.const 1)'],['(i32.const -1)'],['(i32.const -2147483648)']],
          'crc32word':[['(i32.const 0)','(i32.const 0)'],['(i32.const -1)','(i32.const 42)'],['(i32.const -2147483648)','(i32.const 2147483647)'],['(i32.const 123)','(i32.const 456)']],
          'mixed4':[['(i32.const 0)','(i64.const 0)','(f64.const -0)','(i32.const 1)'],['(i32.const -1)','(i64.const -1)','(f64.const inf)','(i32.const -1)'],['(i32.const 123)','(i64.const 9223372036854775807)','(f64.const 3.125)','(i32.const 456)'],['(i32.const -2147483648)','(i64.const -9223372036854775808)','(f64.const -inf)','(i32.const 2147483647)']],
          'memory16':[['(i32.const 0)','(i32.const 1)','(i32.const 1)'],['(i32.const 0)','(i32.const -2147483648)','(i32.const -1)'],['(i32.const 65532)','(i32.const 42)','(i32.const 0)'],['(i32.const -1)','(i32.const 1)','(i32.const 1)']]
        }[row['kernel']]
        text=t.w.emit(mod)
        wrappers=' '.join(f'(func (export "test{i}") (result i32) (call 0 {" ".join(args)}))' for i,args in enumerate(cases))
        wat=text[:-1]+wrappers+')';tag=src.stem+'-'+row['kernel'];wp=p/(tag+'.wat');binary=wp.with_suffix('.wasm')
        wp.write_text(wat,encoding='utf-8');t.w.tool('wat2wasm',[wp,'-o',binary])
        log=t.w.tool('wasm-interp',[binary,'--run-all-exports']);wp.with_suffix('.log').write_text(log)
        values=[]
        for line in log.splitlines():
            if line.startswith('test'):
                match=re.search(r'=> i32:(\d+)',line)
                values.append(int(match[1]) if match else 'trap' if 'error:' in line else 'unparsed:'+line)
        assert len(values)==4,(tag,log)
        report.append({'kernel':row['kernel'],'variant':row['variant'],'opt':row['opt'],'outputs':values,'raw_log':str(wp.with_suffix('.log').relative_to(out)).replace('\\','/')})
    references={x['kernel']:x['outputs'] for x in report if x['variant']=='plain' and x['opt']=='raw'}
    bad=[x for x in report if x['outputs']!=references[x['kernel']]]
    save(out/'interpreter.json',{'conditions':len(report),'calls':4*len(report),'mismatches':len(bad),'rows':report})
    if bad:raise AssertionError(bad)


def main(out):
    rows=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    checker=Path(__file__).with_name('check.cjs')
    result=subprocess.run(['node',str(checker),str(out),'check'],capture_output=True,text=True,timeout=90)
    (out/'correctness.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    print(result.stdout.strip(),flush=True)
    interpreter(out,rows);print('WABT interpreter complete',flush=True)
    order=[(row,rep) for rep in range(3) for row in rows];random.Random(20261018).shuffle(order)
    perf=[]
    for i,(row,rep) in enumerate(order):
        r=subprocess.run(['node',str(checker),str(out),'performance',row['path'],row['kernel']],capture_output=True,text=True,timeout=30)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        perf.append({'replicate':rep,'variant':row['variant'],'opt':row['opt'],**json.loads(r.stdout)})
        save(out/'performance.json',perf)
        if (i+1)%42==0:print('performance',i+1,'/',len(order),flush=True)
    summary=[]
    for row in rows:
        samples=[r for r in perf if r['file']==row['path']]
        medians=[r['median_ns'] for r in samples]
        summary.append({'kernel':row['kernel'],'variant':row['variant'],'opt':row['opt'],'bytes':row['bytes'],
                        'runtime_median_ns':statistics.median(medians),'process_medians_ns':medians,
                        'analysis_median_ms':row['analysis_ms']['median'],'analysis_range_ms':[row['analysis_ms']['min'],row['analysis_ms']['max']],
                        'linear_memory_bytes':samples[0]['linear_memory_bytes'],'max_rss_kib':[r['max_rss_kib'] for r in samples]})
    save(out/'summary.json',summary)
    lines=['|Kernel|Variant|Opt|Bytes|Runtime ns (median of 3 processes)|Process medians ns|Analysis ms|','|---|---|---|---:|---:|---|---:|']
    for x in summary:lines.append('|'+ '|'.join([x['kernel'],x['variant'],x['opt'],str(x['bytes']),f"{x['runtime_median_ns']:.2f}",', '.join(f'{v:.2f}' for v in x['process_medians_ns']),f"{x['analysis_median_ms']:.4f}"])+'|')
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for name in ['finish.py','check.cjs','transform.py']:
        shutil.copy2(Path(__file__).with_name(name),out/('final-source-'+name))
    print('finish complete',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();main(a.output)
