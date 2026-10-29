# -*- coding: utf-8 -*-
"""Audit saved evidence and create a dated analysis, without rerunning timings."""
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=ROOT/'results/invention-20261019'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    main=BASE/'relaxed-carrier-v2';comp=BASE/'relaxed-compare-v2';rows=read(main/'summary.json');a=read(comp/'analysis.json');bench=read(main/'benchmark.json');ts=read(main/'transforms.json')
    check=read(main/'correctness.json');check2=read(comp/'correctness.json');engine=read(BASE/'relaxed-verify-v1/interpreter.json');engine2=read(BASE/'relaxed-compare-verify-v1/interpreter.json')
    assert len(rows)==48 and check['calls']==48*5197 and check['mismatches']==0
    assert check2['calls']==54*5197 and check2['mismatches']==0 and len(a)==18
    assert engine['calls']==288 and engine2['calls']==324
    assert all(read(main/'replay.json').values())
    for r in rows:assert sha(main/r['path'])==r['sha256']
    env=read(main/'environment.json')
    for name in ('prototype.py','run.py','bench.cjs','check.cjs','verify.py'):
        relative=str((HERE/name).relative_to(ROOT));assert sha(HERE/name)==env['source_sha256'][relative]
    for path,value in read(comp/'script-hashes.json').items():assert sha(Path(path))==value
    equal=[]
    for model in ('majority','mix4','mix16'):
        for opt in ('raw','O3'):
            x=comp/(model+'.dynamic.'+opt+'.family.recovered.wasm');y=comp/(model+'.relaxed.'+opt+'.family.recovered.wasm')
            equal.append(dict(model=model,opt=opt,same_bytes=x.read_bytes()==y.read_bytes()))
    assert all(x['same_bytes'] for x in equal)
    def row(model,mode):return next(r for r in rows if r['model']==model and r['mode']==mode and r['opt']=='O3' and 'kind' not in r)
    def attack(model,mode,kind='family'):return next(r for r in a if r['model']==model and r['mode']==mode and r['opt']=='O3' and r['attack']==kind)
    lines=['# 実測と判定（2026-10-19）','','主値は `relaxed-carrier-v2` と `relaxed-compare-v2`。v1主実装とv2再実行の48本はbyte一致。性能は各実験の測定で変動する。','','## O3のサイズと実行時間','','時間は3 fresh processそれぞれの11標本の中央値を取り、その3値の中央値。単位ns/呼出し。JS→Wasm呼出し・入力選択の費用を含み、純粋な命令レイテンシではない。','','| kernel | plain bytes / ns | dynamic bytes / ns | relaxed bytes / ns | relaxed / plain 実行 |','|---|---:|---:|---:|---:|']
    for model in ('majority','mix4','mix16'):
        x,y,z=[row(model,mode) for mode in ('plain','dynamic','relaxed')]
        lines.append(f"| {model} | {x['bytes']} / {x['median_ns']:.2f} | {y['bytes']} / {y['median_ns']:.2f} | {z['bytes']} / {z['median_ns']:.2f} | {z['median_ns']/x['median_ns']:.2f}x |")
    lines+=['','## 方式既知の解析','','回復先は同じモデル・同じ最適化条件でdynamic/relaxedの6組すべてbyte一致した。元ソースの構文が同じという意味ではない。以下のcore時間は既に読み込んだASTへの11回処理の中央値。外部ツール起動・読込み・生成・最適化時間はJSONで別記した。','','| kernel | dynamic系列 ms | relaxed系列 ms | relaxed範囲 ms | 両方式の回復 bytes |','|---|---:|---:|---:|---:|']
    for model in ('majority','mix4','mix16'):
        x,y,z=attack(model,'dynamic'),attack(model,'relaxed'),attack(model,'relaxed','range')
        lines.append(f"| {model} | {x['analysis_median_ms']:.4f} | {y['analysis_median_ms']:.4f} | {z['analysis_median_ms']:.4f} | {y['recovered_bytes']} |")
    lines+=['','範囲解析は既知bitを各命令へ伝播するため追加の処理がある。これだけをdynamicのpattern置換と比べれば約2〜3倍になるが、系列特化の共通探索器では一貫した増加がなかった。この実装差を難読化強度と解釈しない。通常のO3収束実行だけではrelaxedの179/639/2168 byteが残るため、「通常最適化には残る」と「方式既知の回復に追加費用を課す」は分けて扱う。','','## 正当性・対照','','- 主48本：249,456呼出し。各2,197境界値組＋3,000ランダム入力。値不一致0、trap0。','- 補助54本：280,638呼出し、不一致0。主と補助を合計すると530,094呼出しだが、同一内容のバイナリや入力を含む。','- WABT別エンジン：主288＋補助324＝612呼出し、不一致0。','- 4bit全列挙と32bitランダムを合わせた9,096組について281,976局所恒等式チェック、不一致0。誤ったANDは7,799組で失敗。補助検証でも同じ代数チェックを再実行したが、独立の新しいデータセットとは数えない。','- in-range/未知indexは零と判定しない。divisionとmemoryは変換・回復の両方で拒否。','- 出力がmaskに依存する対照では、Nodeのrelaxed値-1を精密化すると0となった。dynamicにも結果が変わる対照がある。条件付き回復を一般同値変換と誤記しない。','','全入力の機械証明ではない。本文の代数説明と有限テストの役割を分ける。この対象範囲の実行ツールにはunsupported/crash/timeoutはなかった。NotDec・StackSight・人間解析は未実行であり、成功/失敗の集計に入れない。','','## 費用と測定条件','']
    rss=[b['maxRSS_KiB'] for b in bench];rt=[t['transform_ms'] for t in ts if t['mode']=='relaxed'];heaps=[x['python_heap_peak_bytes'] for x in a]
    lines += [f"環境：{env['cpu']}、{env['logical_cpus']} logical CPU、{env['os']}、Node {env['node']} / V8 {env['v8']}、Python {env['python']}、WABT 1.0.42、Binaryen 133。CPU affinity・周波数は固定していない。",'',f"90プロセスをserialで実行。各10,000回warmup、11×3,000呼出し。RSS最大値の観測範囲は{min(rss)}〜{max(rss)} KiB。これはNodeプロセス全体のhigh-water markで、Wasmだけのメモリ消費を表さない。線形memoryは全条件0 page。O3 relaxedのlocal数は3/2/12。",'',f"relaxed変換は各モデル1回の観測で{min(rt):.2f}〜{max(rt):.2f} ms。外部ツールの起動・validate・読書きを含み、統計的な変換速度比較ではない。適応的解析のPython heap peakは{min(heaps)}〜{max(heaps)} byte。生標本、process間の範囲、サイズ、localsはJSONへ保存。",'','## 判断と次の設計制約','','この限定案は主発明にしない。理由は解除できたからではなく、既知maskingへの供給源変更を超える技術差と、dynamic対照に対する追加の保護優位性が示せなかったため。通常最適化に残ることだけを特許・論文の根拠にしない。','','次案では、実装依存の値を追加する前に、生成規則を知る解析者がその値を合法な定数へ固定して保護機構を除去できるか検査する。これは一般の難読化の不可能性ではなく、今回の出力独立maskへの設計上の制約である。研究全体の独自で有効な主発明、特許性の確立は未達。']
    (HERE/'analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    links=[]
    for doc in HERE.glob('*.md'):
        text=re.sub(r'```[\s\S]*?```','',doc.read_text(encoding='utf-8'))
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            if '://' in link or link.startswith('#'):continue
            dest=(doc.parent/link.split('#')[0]).resolve();assert dest.exists(),(doc,link);links.append(str(dest))
    record=dict(primary_binaries=48,primary_calls=check['calls'],supplementary_binaries=54,supplementary_calls=check2['calls'],second_engine_calls=engine['calls']+engine2['calls'],replay_bytes_equal=48,paired_recoveries=equal,local_links_checked=len(links),main_invention_established=False,goal_complete=False,files_sha256={str(f.relative_to(ROOT)):sha(f) for f in HERE.glob('*') if f.is_file()})
    target=BASE/'relaxed-final-audit-v1.json'
    with target.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in record.items() if k not in ('files_sha256','paired_recoveries')}))
if __name__=='__main__':main()
