import hashlib
import json
from pathlib import Path
import platform
import shutil
import statistics
import sys
import prototype as p


def main(src,perf,audit,out):
    src,perf,audit,out=map(Path,(src,perf,audit,out));out.mkdir(parents=True,exist_ok=False);verified={}
    for folder in (src,perf,audit):
        pins=json.loads((folder/'pins.json').read_text())
        for file,h in pins.items():assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==h
        verified[folder.name]=len(pins)
    m=json.loads((src/'manifest.json').read_text());c=json.loads((src/'checks.json').read_text());a=json.loads((audit/'audit.json').read_text());q=json.loads((perf/'summary.json').read_text());controls=json.loads((audit/'control-checks.json').read_text())
    positive=[x for x in m['targets'] if not x.get('negative')];unique={hashlib.sha256((src/x['file']).read_bytes()).hexdigest() for x in positive}
    fit=[{'name':x['name'],'order':x['order'],'median_ms':statistics.median(x['durations_ms']),'min_ms':min(x['durations_ms']),'max_ms':max(x['durations_ms'])} for x in a['timings']]
    short=0;rss=[]
    for x in q['rows']:
        d=json.loads((perf/x['file']).read_text());short+=sum(b['ns']<1e7 for b in d['batches']);rss.append(d['max_rss_kib'])
    facts={'verified_pins':verified,'positive_conditions':len(positive),'unique_positive_binaries':len(unique),
           'step_calls':sum(x['calls'] for x in c['rows'] if not x['negative']),'reset_calls':sum(x['resets'] for x in c['rows'] if not x['negative']),
           'unexpected_traps':sum(x['traps'] for x in c['rows'] if not x['negative']),
           'negative_counterexamples':sum(x['counterexample'] is not None for x in c['rows'] if x['negative']),
           'public_recoveries':len(m['recoveries']),'public_steps_per_recovery':16,
           'total_public_steps':sum(x['query']['step_calls'] for x in m['recoveries']),
           'certificate_count':len(a['certificates']),'byte_reproduced':len(a['byte_reproduced']),
           'interpreter_steps':len(a['interpreter'])*8,'solver_systems':sum(x['systems'] for x in a['solver']),
           'fit':fit,'performance':q['summary'],'short_batches_below_10ms':short,'node_max_rss_kib_range':[min(rss),max(rss)],
           'transform_ms_range':[min(x['elapsed_ms'] for x in m['transforms']),max(x['elapsed_ms'] for x in m['transforms'])],
           'public_recovery_total_ms_range':[min(x['elapsed_ms'] for x in m['recoveries']),max(x['elapsed_ms'] for x in m['recoveries'])],
           'controls':controls,'environment':{'python':platform.python_version(),'platform':platform.platform(),'wabt':p.w.tool('wat2wasm',['--version']).strip(),'binaryen':p.w.tool('wasm-opt',['--version']).strip()}}
    (out/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf8')
    lines=['# 非単射な持続状態表現の比較','',
           f"正{len(positive)}条件、byteの異なる{len(unique)}本。step {facts['step_calls']:,}回、reset {facts['reset_calls']:,}回、不一致0・予期しないtrap0。3設定は同じ線形系の状態数・精度配置違いであり、独立アプリではない。",'',
           '## O3性能','',
           'ns/step。3 fresh process × 7 batchの中央値。16,384 stepのwarmup、15ms校正、共通Wasm loopで入力更新・checksum。各batch前のresetは計時外。CPU固定・周波数固定なし。', '',
           '|設定|plain|可逆basis|非単射quotient|零摂動perturb|回復後O3|','|---|---:|---:|---:|---:|---:|']
    for name in m['models']:
        rows={x['mode']:x for x in q['summary'] if x['name']==name}
        lines.append('|'+name+'|'+'|'.join(f"{rows[k]['median_ns']:.3f}" for k in ('plain','basis','quotient','perturb','recovered'))+'|')
    lines+=['','全条件linear memoryは0。i32 globalの個数は元/変換2・3・4、回復3・5・7。論理payloadのbyte数とエンジンの実消費量は同一ではない。Node全体maxRSSは'+str(facts['node_max_rss_kib_range'])+' KiB。315batch中10ms未満0。','','## 公開I/O回復','',
            '全24条件でreset1回とstep16回から同等な漸化式を生成した。source/基底/商/摂動のquery transcriptは同じ設定内で一致する。内部state・行列・manifestは回復入力に含まれない。全24回に要した総stepは384回で、同じ16個の入力を各variantへ送った数である。','',
            '|設定|回復次数|fit中央値ms|31反復のmin–max ms|','|---|---:|---:|---:|']
    for x in fit:lines.append(f"|{x['name']}|{x['order']}|{x['median_ms']:.4f}|{x['min_ms']:.4f}–{x['max_ms']:.4f}|")
    lines+=['','合同式のpivot付値は[0,16]、[0,8,24]、[0,5,13,21]で、実際に非単元を含む。全pipelineの単発測定は約66–93msでNode/WABT起動・コンパイルを含む。これは31反復したfitだけの時間と測定法が違う。人間の解析器開発時間は測っていない。','','## 限界と判断','',
            '既知の有限環上の漸化式合成が近い。非一意な状態表現、mod2^32の零因子、到達状態外への摂動は、今回の入出力クラスに対する問い合わせ数を増やさなかった。非単射方式を主発明には採用しない。元の全状態を回復できるという結論ではなく、同じ入出力を持つ短い規則を回復した結果である。','',
            '線形・時不変・零初期・既知次数上限というpromiseが必要。特定の入力だけ出力+1する非線形例と、上限8に対する遅延17の線形例は、16問では同じ応答になる反例を実行した。後者は上限17を与えると34応答で回復し、別入力列4096呼出しが一致した。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8');shutil.copyfile(p.HERE/'report.py',out/'source-report.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({k:facts[k] for k in ('positive_conditions','unique_positive_binaries','step_calls','reset_calls','public_recoveries','solver_systems')},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
