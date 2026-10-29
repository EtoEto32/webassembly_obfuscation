"""Aggregate authoritative logs, snapshot sources, and pin evidence hashes."""
import hashlib,json,os,platform,shutil,statistics,subprocess,sys
from pathlib import Path
import prototype as p
main,runtime,extra,audit,model,selection,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
read=lambda f:json.loads(f.read_text(encoding='utf-8'))
checks=read(main/'checks.json')['results'];parallel=read(main/'concurrency.json')['results'];ex=read(extra/'checks.json');au=read(audit/'audit.json');times=read(runtime/'summary.json')
positive=[x for x in checks if not x['negative']];manifest=read(main/'manifest.json');meta={r['file']:r for r in manifest}
encoded=[x for x in positive if meta[x['file']]['mode']!='plain'];by={x['mode']:x for x in times}
result=dict(main_positive_conditions=len(positive),main_positive_calls=sum(x['calls'] for x in positive),main_positive_traps=sum(x['traps'] for x in positive),
    encoded_recovery_conditions=len(encoded),encoded_recovery_success=sum(x['memoryRecovered'] for x in encoded),
    attack_ms_range=[min(x['identificationMsIncludingInstantiation'] for x in encoded),max(x['identificationMsIncludingInstantiation'] for x in encoded)],
    extra_conditions=len(ex),extra_paired_calls=sum(x['calls'] for x in ex),extra_paired_traps=sum(x['traps'] for x in ex),
    parallel_positive_conditions=sum(not x['negative'] for x in parallel),parallel_positive_operations=sum(x['operations'] for x in parallel if not x['negative']),
    ticket_negative_results=[x for x in parallel if x['negative']],and_negative_witnesses=[x['witness'] for x in checks if x['witness']],
    replay_binaries=len(au['replay']),wabt_calls=sum(len(x['actual']) for x in au['wabt']),rejections=len(au['rejections']),
    model_candidates=sum(x['affine_candidates'] for x in read(model/'model.json')),model_checks=sum(x['checks'] for x in read(model/'model.json')),
    runtime=times,native_neg_time_reduction=1-by['native-neg']['median_ns']/by['cas-neg']['median_ns'],
    native_affine_time_reduction=1-by['native-affine']['median_ns']/by['cas-affine']['median_ns'])
assert all(x['witness'] is None for x in positive) and all(x['memoryRecovered'] for x in encoded)
assert all(x['valid'] for x in parallel if not x['negative']) and all(x['match'] for x in ex+au['replay'])
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
env=dict(os=platform.platform(),processor=platform.processor(),processor_identifier=os.environ.get('PROCESSOR_IDENTIFIER'),logical_processors=os.cpu_count(),python=sys.version,
    node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.q.w.tool('wat2wasm',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip(),
    runtime_flags=['--no-liftoff','--no-wasm-lazy-compilation'],cpu_affinity_fixed=False,frequency_fixed=False,cim_cpu_query='access failed; environment identifier used')
(out/'environment.json').write_text(json.dumps(env,indent=2),encoding='utf-8')
lines=['# アトミック表現の実測比較','','同じcounter入力のO3、競合なし、Wasm内部fetch-add loop。3 fresh process × 9 batch。値はprocess中央値の中央値。min/maxは信頼区間ではない。','','|方式|ns / update|min–max ns|binary bytes|','|---|---:|---:|---:|']
for r in times:lines.append(f'|{r["mode"]}|{r["median_ns"]:.4f}|{r["min_ns"]:.4f}–{r["max_ns"]:.4f}|{r["bytes"]}|')
lines+=['',f'同一codecのCAS対照からの時間短縮：反転 {100*result["native_neg_time_reduction"]:.2f}%、affine {100*result["native_affine_time_reduction"]:.2f}%。',
 '全条件の線形memoryは65536 bytes。RSSはNode全processの最大値であり符号化単体の使用量ではない。',
 '並行試験の実行件数をこの競合なし性能測定の反復数へ加算しない。共有初期化・compile・instantiateを計時外とし、各batch前の公開storeも計時外。',
 '公開storeによる識別時間はWasm compile/instantiateを含む各1回の診断値。人の攻撃開発時間や一般逆コンパイル費用は測っていない。']
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
here=Path(__file__).parent
sources=list(here.glob('*.py'))+list(here.glob('*.cjs'))+list(here.glob('*.md'))+[p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
snap=out/'sources';snap.mkdir();pins={}
for f in sources:
    name=f.relative_to(p.ROOT).as_posix().replace('/','__');shutil.copyfile(f,snap/name)
    pins[f.relative_to(p.ROOT).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
for folder in (main,runtime,extra,audit,model,selection):
    for f in folder.rglob('*'):
        if f.is_file():pins[f.relative_to(p.ROOT).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
for f in (out/'report.json',out/'environment.json',out/'comparison.md'):
    pins[f.relative_to(p.ROOT).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
(out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)}));print(json.dumps(dict(pins=len(pins))))
