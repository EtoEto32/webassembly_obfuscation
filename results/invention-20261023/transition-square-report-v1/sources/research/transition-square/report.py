# -*- coding: utf-8 -*-
import json,platform,shutil,statistics,subprocess,sys
from pathlib import Path
import prototype as p

def main(main_dir,audit_dir,perf_dir,rounds_dir,dest):
    main_dir,audit_dir,perf_dir,rounds_dir,out=map(lambda x:Path(x).resolve(),(main_dir,audit_dir,perf_dir,rounds_dir,dest))
    out.mkdir(parents=True,exist_ok=False)
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    checks=read(main_dir/'checks.json');audit=read(audit_dir/'audit.json');perf=read(perf_dir/'summary.json');rounds=read(rounds_dir/'summary.json')
    attacks=read(main_dir/'attacks.json');transforms=read(main_dir/'transforms.json');manifest=read(main_dir/'manifest.json')
    facts={'positive_conditions':len(checks['positive']),'calls':checks['calls'],'mismatches':checks['mismatches'],'traps':checks['traps'],'negative_conditions':len(checks['negative']),
      'recovered':sum(a['status']=='success' for a in attacks),'unsupported':sum(a['status']=='unsupported' for a in attacks),'recovery_ms_range':[min(a['milliseconds'] for a in attacks),max(a['milliseconds'] for a in attacks)],
      'square_root_ms_range':[min(a['root_ms'] for a in attacks if a['denominator']==16),max(a['root_ms'] for a in attacks if a['denominator']==16)],
      'transform_ms_range':[min(a['milliseconds'] for a in transforms if a['mode']!='bad-square'),max(a['milliseconds'] for a in transforms if a['mode']!='bad-square')],
      'small_graphs':audit['model_graphs'],'partitions':audit['model_partition_checks'],'smt_unsat':len(audit['smt']),'wabt_calls':audit['wabt_calls'],'rejection_controls':len(audit['rejected_controls']),
      'runtime_processes':perf['processes'],'runtime_batches':perf['batches'],'runtime_batches_under_10ms':perf['under_10ms'],'round_probe':rounds['wasm_check'],'rows':[]}
    table=['|例 / graph状態数|元 ns|base ns|square ns|回復 ns|square/base|square/元|元/base/square bytes|','|---|---:|---:|---:|---:|---:|---:|---|']
    for name in ('bits4','bits8','bits12'):
        rr={r['mode']:r for r in perf['rows'] if r['name']==name};n=next(r['nodes'] for r in manifest if r['name']==name and r.get('nodes'))
        ratio=rr['square']['median_ns']/rr['base']['median_ns'];overall=rr['square']['median_ns']/rr['plain']['median_ns']
        facts['rows'].append({'name':name,'nodes':n,'square_over_base':ratio,'square_over_plain':overall,'runtime':rr})
        table.append(f"|{name} / {n}|{rr['plain']['median_ns']:.3f}|{rr['base']['median_ns']:.3f}|{rr['square']['median_ns']:.3f}|{rr['square-recovered']['median_ns']:.3f}|{ratio:.4f}|{overall:.1f}|{rr['plain']['core_bytes']}/{rr['base']['core_bytes']}/{rr['square']['core_bytes']}|")
    p.q.save(out/'summary.json',facts)
    report='''# 遷移二乗による双模倣評価の実測

2026-10-23。新規性未確認の候補を実Wasmへ実装した。**主特許候補には不採用**。回路還元と行列関数の既知原理に近く、正当性の根拠と同じ主平方根から全対象を解除できた。

## 正当性と回復

元の3式は4/8/12個の入力bitから0/1を返す。3製品・3実アプリの比較ではない。各式の全bit割当て16/256/4,096に4境界入力と512個の全32bit乱数を追加し、532/772/4,612入力を使った。高位bitを含む全2^32入力を実行したという意味ではない。

元、base、square、回復の正54条件で106,488呼出し一致、予期しないtrap0。最適化raw/O3と2つのstate番号置換を含む。単純なP^2へ置き換えた負12条件にはすべて反例がある。v2との共通入力・共通binaryを独立標本として合算しない。

公開binaryだけを渡した回復器はbase12条件・square12条件すべてで等価Wasmを生成した。whole pipelineは約0.25–0.40秒、squareの行列逆算は約3.85–115.06ms、Boolean抽出は約0.17–0.92ms。これは各条件1回の診断値であり、安定した分布や最良攻撃性能とはしない。whole pipelineの大部分は固定profileを検査する外部ツール起動である。元のbyte列完全再現を要求せず、出力BDDの同値性を判定した。

24件のsource Boolean ASTと抽出BDDの不一致式はZ3でUNSAT。これはその式同士の全32bit入力同値であり、Wasm処理系や変換器全体の形式証明ではない。別のWABT interpreterで正54本×3入力=162呼出しを照合した。未対応source-memory/source-addと、実行意味を書き換えたevaluatorの3対照を拒否した。

n=2..5のleaf自己loop以外DAGのbinary分岐graphを全列挙し、682 graphで平方根の元行列一致、32,916 partitionでP/Qのlumpability一致を確認。これは限定小モデルの全数検査。一般の論証は[設計](../../../research/transition-square/algorithm.md)に分けて記録した。

## 性能

TABLE

各variant3 fresh process×7batch、全36process/252batch。warmup16,384呼出し、20msを目標に回数を校正し、10ms未満のbatchは0。表は各processのbatch中央値を取り、その3中央値の中央値。Node24.15.0/V8 13.6.233.17-node.48、--no-liftoff --no-wasm-lazy-compilation、WABT1.0.42、Binaryen133。CPU affinity・周波数は固定していない。

coreをO3にした後にWasm内のLCG入力更新・rolling checksum・反復wrapperを追加し、同じ条件で測った。wrapperの144呼出し比較は一致。回復coreは生成後のO3を追加していない。wrapperのコストも表に含む。元の短い式はJITでinline可能なため、ns値を実アプリ全体の費用へ一般化しない。

base/squareはいずれも私有linear memory65,536bytes、元/回復は0。全Node process peak RSSは約35–36MiBで、JIT等も含む。最小保存bit数やWasm単独peak memoryの測定ではない。生成時間はsummary.jsonのtransform_ms_rangeに単発値として保存した。型・memory構造回復率やDisrobe/NotDec本体の耐性はこの実験では測っていない。

## 速くなった理由と不採用理由

squareは同じ単純なdense partition評価器のbaseより約26–37%短い。一方、通常の式に対しては約811–8,643倍の実行費用で、追加保護は強くない。既存の最良bisimulation implementationに勝ったという比較ではない。

診断専用のround counterを持つ別Wasmを作り、8,736呼出しでPythonモデルと実Wasmの反復回数・結果を照合した。4/8/12bitの平均反復回数はbaseが3.4375/4.9258/6.0955、squareが2.5000/3.1211/4.1794。2段先の違いを一度に伝播でき、必要反復が減ることが高速化と整合する。診断Wasmは性能測定に使っていない。

成功した動作、比較上の高速化、独立した難読化の新規性は分ける。元の計算を別の問題へ移しただけで保護が強まるとは言えない。今回の意味保存はQからPを多項式で戻せることに依存し、公開supportと正確な三角平方根がその逆変換を実際に与えた。この理由から、指数やseedの調整を続ける主案にはしない。

## 失敗ログ・再現性

v1は--enable-bulk-memory不足で中断した。v2は差分正当性に一致したが、O3の12条件をprofile未対応とした。双方のoptimizer byte固定点まで正規化するv3ではすべて回復した。これらを保護成功には加算しない。コードの修正であり、三つの発明ではない。

[READMEの再現CLI](../../../research/transition-square/README.md)、[近接先行技術・閲覧範囲](../../../research/transition-square/prior-art.md)。各runの生データ、各出力Wasm/WAT、外部interpreterログ、SMT結果、失敗資料を保存している。source snapshotとSHA256照合表を本directoryへ収録した。外部公開・pushはしていない。主発明の研究は未完了である。
'''.replace('TABLE','\n'.join(table))
    (out/'report.md').write_text(report,encoding='utf-8')
    environment={'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'node':checks['node'],'v8':checks['v8'],'z3':audit['z3'],'wabt':p.q.w.tool('wasm-validate',['--version']).strip(),'binaryen':p.q.w.tool('wasm-opt',['--version']).strip(),'date':'2026-10-23'}
    p.q.save(out/'environment.json',environment)
    sources=[f for f in p.HERE.iterdir() if f.suffix in ('.py','.md','.cjs')]+[p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/span-mask/bench.cjs']
    for src in sources:
        target=out/'sources'/src.relative_to(p.ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    files=sources+[f for d in (main_dir,audit_dir,perf_dir,rounds_dir,out) for f in d.rglob('*') if f.is_file()]
    p.q.save(out/'sha256.json',[{'file':str(f.relative_to(p.ROOT)).replace('\\','/'),'sha256':p.q.digest(f)} for f in files])
    print(json.dumps({'calls':facts['calls'],'recovered':facts['recovered'],'hashes':len(files),'ratios':[(r['name'],r['square_over_base'],r['square_over_plain']) for r in facts['rows']]}))
if __name__=='__main__':main(*sys.argv[1:])
