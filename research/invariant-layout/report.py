import argparse,hashlib,json,statistics
from pathlib import Path

def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def run(main,audit,runtime,analysis,model,output):
    main,audit,runtime,analysis,model=map(lambda x:Path(x).resolve(),(main,audit,runtime,analysis,model));out=Path(output).resolve()
    if out.exists():raise FileExistsError(out)
    hashes={};pins={};producers=[]
    def read(d,n):
        f=d/n;hashes[str(f)]=digest(f);return json.loads(f.read_text(encoding='utf8'))
    for d in (main,audit,runtime,analysis):
        manifest=read(d,'pins.json')
        for f,h in manifest.items():assert digest(d/f)==h,(d,f)
        pins[d.name]=len(manifest)
        for saved in d.glob('source-*'):
            current=Path(__file__).parent/saved.name.removeprefix('source-')
            assert current.exists() and digest(current)==digest(saved),current
            producers.append(str(saved))
    checks=read(main,'checks.json');attacks=read(main,'analysis.json');transforms=read(main,'transforms.json')
    pos=[x for x in checks['results'] if not x['negative']];neg=[x for x in checks['results'] if x['negative']]
    assert all(x['mismatch']==0 for x in pos) and all(x['mismatch']>0 for x in neg)
    good=[x for x in attacks if x['mode']!='bad'];assert len(good)==18 and all(x['status']=='recovered_candidate' for x in good)
    assert all(x['status']=='rejected' for x in attacks if x['mode']=='bad')
    replay=read(audit,'replay.json');assert all(x['byte_equal'] for x in replay)
    interp=read(audit,'interpreter.json');pages=read(audit,'page-summary.json');models=read(model,'model.json');wide=read(audit,'wide-model.json')
    runtime_rows=read(runtime,'runtime.json');rt=read(runtime,'summary.json');ab=read(analysis,'summary.json');samples=read(analysis,'measurements.json')
    assert rt['processes']==len(runtime_rows)==45 and rt['batches']==405 and len(samples)==63
    assert all(x['identification_calls']==1024 for x in samples)
    for row in rt['rows']:
        for mode,values in row['modes'].items():
            measured=[x['measurement']['medianNs'] for x in runtime_rows if x['name']==row['name'] and x['mode']==mode]
            assert len(measured)==3 and statistics.median(measured)==values['median']
    facts=dict(positive_conditions=len(pos),inputs=checks['inputs'],positive_calls=sum(x['calls'] for x in pos),expected_traps=sum(x['traps'] for x in pos),negative_conditions=len(neg),recovery_candidates=len(good),
      regenerated=len(replay),interpreter_value_calls=sum(x['value_calls'] for x in interp),interpreter_trap_calls=sum(x['trap_calls'] for x in interp),interpreter_memory_probes=sum(x['memory_probes'] for x in interp),
      extra_pages=pages,small_model_cases=models['update_cases'],wide_model_cases=wide['cases'],
      rss_kib=[min(x['measurement']['maxRssKiB'] for x in runtime_rows),max(x['measurement']['maxRssKiB'] for x in runtime_rows)],
      transform_ms=[min(x['transform_ms'] for x in transforms if x['mode']!='bad'),max(x['transform_ms'] for x in transforms if x['mode']!='bad')],
      runtime=rt,analysis=ab)
    lines=['# 値依存配置の実測集計','',
      f"主実験は3種類の小さな状態更新kernel。正{len(pos)}条件、共通{checks['inputs']}入力列、{facts['positive_calls']:,}呼出し（期待trap {facts['expected_traps']:,}件）で戻り値・trap有無・復号した全メモリが一致。負{len(neg)}条件はすべて反例を得た。",
      f"公開binaryだけから18/18条件の通常配置候補を構成し、その候補も主実験で比較した。各回復は同じ1,024 helper呼出しで同定する。有限の同定試験は任意binaryの全入力同値性証明ではない。",
      f"{len(replay)}本をbyte一致再生成。別WABT実行器は値{facts['interpreter_value_calls']}、trap {facts['interpreter_trap_calls']}、物理メモリprobe {facts['interpreter_memory_probes']}件を照合。0/2ページの追加8条件{pages['positiveCalls']}呼出しも一致。",
      f"縮小幅1/2/3bitで{models['update_cases']:,}更新を全探索、32bit乱数で{wide['cases']:,}更新を比較。モデル検査と実Wasmの呼出し数は加算しない。",'',
      '## O3実行時間','',
      '単位はWasm wrapperの1反復あたりns。1反復は1～8回の元更新、入力更新、checksumを含む。3 fresh Node processの中央値の中央値で、括弧内はprocess中央値の範囲。', '',
      '| kernel | plain | fixed | full | transport | recovered | transport/full | transport/plain |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in rt['rows']:
        m=x['modes'];cells=[f"{m[k]['median']:.3f} ({m[k]['range'][0]:.3f}–{m[k]['range'][1]:.3f})" for k in ('plain','fixed','full','transport','recovered')]
        lines.append('| '+x['name']+' | '+' | '.join(cells)+f" | {x['transport_over_full']:.3f} | {x['transport_over_plain']:.2f} |")
    lines+=['',f"warmup 16,384、45process・405batch。10ms未満は{rt['short_batches']}batch。各計測前にメモリを初期状態へ戻し、そのコピー時間はtimer外。CPU affinity/周波数は未固定。",'',
      '## 方式既知の回復費用','',
      'O3各条件7回、計63回。WABT読取・計測用binary生成・Node起動・helper同定・候補のコンパイルを含むend-to-end ms。純粋な記号解析時間ではない。', '',
      '| kernel | fixed ms | full ms | transport ms | transport/fixed |',
      '|---|---:|---:|---:|---:|']
    for x in ab['rows']:
        cells=[f"{x['modes'][k]['median']:.2f} ({x['modes'][k]['range'][0]:.2f}–{x['modes'][k]['range'][1]:.2f})" for k in ('fixed','full','transport')]
        lines.append('| '+x['name']+' | '+' | '.join(cells)+f" | {x['transport_over_fixed']:.3f} |")
    lines+=['', '差分移送は同じ動的表現のfull版より約12～19%速かった。固定配置に対する回復時間の中央値比は約1.017～1.055で、範囲は重なる。問い合わせ数の増加はない。全体復号を省く実行改善と、追加保護効果を区別する。', '',
      f"全本体はlinear memory 64KiB、追加配置表・追加ページは0。Node maxRSSは{facts['rss_kib'][0]:,}–{facts['rss_kib'][1]:,}KiBで実行環境全体を含む。変換時間は単回測定で{facts['transform_ms'][0]:.2f}–{facts['transform_ms'][1]:.2f}ms。本体サイズはfacts.jsonのbinariesに保存。",'',
      '既存の動的符号化との独立性、実用的な保護優位、実アプリでの適用率は未確立。今回の公開統計量は実行側と解析側の双方に安い配置の復元手順を与えるため、主発明への採用は見送る。', '']
    out.mkdir(parents=True)
    for name,obj in [('facts.json',facts),('verification.json',dict(input_hashes=hashes,verified_pins=pins,producer_snapshots=producers,report_source_sha256=digest(Path(__file__))))]:
        (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
    (out/'pins.json').write_text(json.dumps({x.name:digest(x) for x in out.iterdir()},indent=2),encoding='utf8')
    print(json.dumps(dict(positive_calls=facts['positive_calls'],recovered=len(good),pins=pins)))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','audit','runtime','analysis','model','output'):ap.add_argument(name)
    run(**vars(ap.parse_args()))
