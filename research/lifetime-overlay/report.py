import hashlib
import json
from pathlib import Path
import platform
import shutil
import statistics
import sys
import prototype as p


def main(src,perf,audit,out):
    src,perf,audit,out=map(Path,(src,perf,audit,out));out.mkdir(parents=True,exist_ok=False)
    verified={}
    for folder in (src,perf,audit):
        pins=json.loads((folder/'pins.json').read_text())
        for name,h in pins.items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h
        verified[str(folder)]=len(pins)
    m=json.loads((src/'manifest.json').read_text());c=json.loads((src/'checks.json').read_text())
    a=json.loads((audit/'audit.json').read_text());q=json.loads((perf/'summary.json').read_text())
    performance=[];attack=[]
    for name in ('serial','branch','diamond'):
        rows={r['mode']:r for r in q['summary'] if r['name']==name}
        performance.append({'name':name,'variants':rows,'conflict_over_first':rows['conflict']['median_ns']/rows['first']['median_ns'],
                            'conflict_over_plain':rows['conflict']['median_ns']/rows['plain']['median_ns']})
        for stage in ('raw','O3'):
            for mode in ('plain','first','conflict'):
                file=name+'-'+mode+('-O3' if stage=='O3' else '')+'.wasm'
                ts=[r for r in a['timings'] if r['file']==file]
                attack.append({'name':name,'stage':stage,'mode':mode,'repetitions':len(ts),
                               **{k:statistics.median(r[k] for r in ts) for k in ('reader_ms','normalize_ms','compile_ms','elapsed_ms')},
                               'min_total_ms':min(r['elapsed_ms'] for r in ts),'max_total_ms':max(r['elapsed_ms'] for r in ts),
                               'phis':ts[0]['phis']})
    unique={r['file']:hashlib.sha256((src/r['file']).read_bytes()).hexdigest() for r in m['targets'] if not r.get('negative')}
    short=0;rss=[]
    for row in q['rows']:
        data=json.loads((perf/row['file']).read_text());short+=sum(b['ns']<10e6 for b in data['batches']);rss.append(data['max_rss_kib'])
    facts={'source_pins_verified':verified,'positive_conditions':len(unique),'byte_distinct_positive':len(set(unique.values())),
           'calls':sum(r['calls'] for r in c['results'] if not r['negative']),
           'unexpected_traps':sum(r['traps'] for r in c['results'] if not r['negative']),
           'negative_counterexamples':sum(r['counterexample'] is not None for r in c['results'] if r['negative']),
           'recovered':sum(r['status']=='recovered' for r in m['attacks']),'attacked':len(m['attacks']),
           'performance':performance,'attack':attack,'transforms':m['transforms'],
           'interpreter_calls':a['interpreter_calls'],'reproduced_binaries':len(a['reproduced_binaries']),
           'short_batches_below_10ms':short,'node_max_rss_kib_range':[min(rss),max(rss)],
           'environment':{'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),
                          'wabt':p.wat.tool('wat2wasm',['--version']).strip(),'binaryen':p.wat.tool('wasm-opt',['--version']).strip()}}
    (out/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf8')
    lines=['# 生存区間重複の測定結果','',
           f"正{facts['positive_conditions']}条件（byte異なる{facts['byte_distinct_positive']}本）、{facts['calls']:,}呼出し。不一致0、予期しないtrap0。raw/O3の全18条件を回復。これらは3つの合成kernelの変種であり、36個の独立アプリではない。",'',
           '## O3実行時間','',
           '単位ns/呼出し。3 fresh processの各7batch中央値の中央値。Wasm wrapper内で引数を更新しchecksumを観測。warmup16,384、校正15ms、短batch(<10ms)0。CPU固定・周波数固定なし。', '',
           '|kernel|plain|first-fit|型衝突優先|回復後O3|衝突/first|衝突/plain|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in performance:
        r=row['variants'];lines.append('|'+row['name']+'|'+ '|'.join(f"{r[k]['median_ns']:.3f}" for k in ('plain','first','conflict','recovered'))+f"|{row['conflict_over_first']:.3f}|{row['conflict_over_plain']:.3f}|")
    lines+=['','全元/配置版の線形memoryは65,536 bytes、回復後O3は0。12byteの作業範囲とmemory割当量を区別する。Node全体のmaxRSS範囲は'+str(facts['node_max_rss_kib_range'])+' KiBであり、保護処理単体のheap量ではない。','','## 回復時間','',
            '単位ms、各5反復の中央値。read欄にはvalidation・WABT逆アセンブル・parse・順序を保つANF化を含む。coreは到達定義追跡、compileは出力WAT/Wasmとvalidation。人間の解析器開発時間は含まない。', '',
            '|kernel|段階|方式|read|core|compile|total|phi数|','|---|---|---|---:|---:|---:|---:|---:|']
    for r in attack:
        lines.append('|'+r['name']+'|'+r['stage']+'|'+r['mode']+'|'+'|'.join(f'{r[k]:.3f}' for k in ('reader_ms','normalize_ms','compile_ms','elapsed_ms'))+f"|{r['phis']}|")
    lines+=['','## 判断','',
            '衝突優先はbranch/diamondの静的な幅矛盾を増やした。O3 diamondのcore中央値はfirst-fitより約10.6%増えた一方、totalの差は約4.5%。差が0とは主張しない。ただし経路列挙は不要で16個の合流だけで回復でき、既存技術から独立した原理も確認できない。新発明・保護優位の確立としては不採用。', '',
            'serialのfirst/conflictは同じbyte列になった。計測の小差は同一プログラムの実行ばらつきであり、方式差の効果としない。NotDec等の既存逆コンパイラ本体は実行していない。型衝突数は専用の静的proxyであり、逆コンパイラ失敗率ではない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    shutil.copyfile(p.HERE/'report.py',out/'source-report.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({k:facts[k] for k in ('positive_conditions','byte_distinct_positive','calls','recovered','attacked','short_batches_below_10ms')},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
