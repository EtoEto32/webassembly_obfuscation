import json,os,platform,re,sys
from pathlib import Path
import prototype as p
def main(main,rec,runtime,audit,out):
    main,rec,runtime,audit,out=map(lambda x:Path(x).resolve(),(main,rec,runtime,audit,out));out.mkdir(parents=True,exist_ok=False)
    load=lambda f:json.loads(f.read_text())
    primary=load(main/'checks.json');recovered=load(rec/'checks.json');attacks=load(rec/'recovery.json');perf=load(runtime/'summary.json');au=load(audit/'audit.json')
    assert all(x['status']=='recovered' for x in attacks) and len(attacks)==10
    assert primary['mismatches']==recovered['mismatches']==0
    assert len({tuple(x['output_fingerprints']) for x in attacks})==1
    assert perf['processes']==18 and len({x['correctness_checksum'] for x in perf['samples']})==1
    for row in au['pins']:assert p.q.digest(p.ROOT/row['file'])==row['sha256'],row['file']
    per={x['label']:x for x in perf['conditions']}
    r={'status':'not adopted; novelty and useful protection advantage unestablished','primary':{k:primary[k] for k in ('compress','full_hash','memory_cases','mismatches','corpus_sha256')},'recovery':{k:recovered[k] for k in ('compress','full_hash','mismatches','corpus_sha256')},'all_semantic_fingerprints_equal':True,'distinct_recovered_binary_hashes':au['distinct_recovered_byte_hashes'],'runtime_processes':18,'performance':perf['conditions'],'fiber1_over_plain':per['fiber1-O3']['median_ns']/per['plain-O3']['median_ns'],'fiber1_time_reduction_vs_repair':1-per['fiber1-O3']['median_ns']/per['repair1-O3']['median_ns'],'audit':{k:len(au[k]) for k in ('negative_controls','rejections','byte_reproduction','engines')},'model_pairs':au['model']['exhaustive_state_pairs'],'host':{'platform':platform.platform(),'processor_identifier':os.environ.get('PROCESSOR_IDENTIFIER'),'logical_cpus':os.cpu_count()},'audit_pins_verified':len(au['pins'])}
    lines=['# コピー互換非線形表現：実測比較','','O3、3 fresh processの各7batch中央値の中央値。範囲はprocess中央値の最小–最大。','時間は共通Wasm loop内のSHA-256圧縮1回、RSSはNode全process。','','| 構成 | 時間 ns | 最小–最大 ns | core bytes | linear memory bytes | max RSS中央値 KiB |','|---|---:|---:|---:|---:|---:|']
    for x in perf['conditions']:lines.append(f"| {x['label']} | {x['median_ns']:.3f} | {x['min_ns']:.3f}–{x['max_ns']:.3f} | {x['core_bytes']} | {x['linear_memory_bytes']} | {x['median_max_rss_kib']} |")
    lines.extend(['',f"fiber1/plain={r['fiber1_over_plain']:.3f}倍。素朴repairに対する時間減={100*r['fiber1_time_reduction_vs_repair']:.3f}%。",'','全10入力binaryで同じ1,881演算のDAGを回復。元SHAやcodec metadataを解析器へ渡していない。','repairは最適化された既存ツールの対照ではない。主試験と回復試験は同じ262入力/41メッセージ。','公開標準SHAの機能秘匿の評価ではなく、公開状態APIがない計算における表現除去の検査。'])
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Create report before checking documentation links pointing to it.
    (out/'report.json').write_text(json.dumps(r,indent=2))
    docs=list(Path(__file__).parent.glob('*.md'));links=0
    for f in docs:
        for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if re.match(r'https?://',link):continue
            target=(f.parent/link.split('#')[0]).resolve()
            if not target.exists():raise AssertionError((str(f),str(target)))
            links+=1
    files=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+docs
    files.extend(p.ROOT/f for f in ['research/isotope-swizzle/prototype.py','research/connectivity-elimination/prototype.py','experiments/sha256-research-baseline/vendor/sha256.js','experiments/sha256-research-baseline/vendor/LICENSE'])
    for directory in (main,rec,runtime,audit):files.extend(f for f in directory.iterdir() if f.suffix in ('.json','.wasm'))
    files.extend([p.q.w.WABT/'wasm-validate.exe',p.q.w.WABT/'wasm2wat.exe',p.q.w.WABT/'wat2wasm.exe',p.q.w.WABT/'wasm-interp.exe',p.q.BIN/'wasm-opt.exe'])
    files=sorted(set(f.resolve() for f in files));r['pins']=[{'file':str(f.relative_to(p.ROOT)),'sha256':p.q.digest(f)} for f in files];r['local_doc_links_checked']=links
    (out/'report.json').write_text(json.dumps(r,indent=2));print(json.dumps({'pins':len(files),'links':links,'main_compress':primary['compress'],'main_hash':primary['full_hash'],'recovered_compress':recovered['compress'],'recovered_hash':recovered['full_hash']}))
if __name__=='__main__':main(*sys.argv[1:])
