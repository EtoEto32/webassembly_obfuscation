# -*- coding: utf-8 -*-
import collections,json,statistics
from pathlib import Path
import prototype as q
ROOT=q.ROOT;HERE=Path(__file__).resolve().parent;R=ROOT/'results/invention-20261019'
def read(folder,name):return json.loads((R/folder/name).read_text(encoding='utf-8'))
def main():
    correctness=read('concurrent-frontier-v2','correctness.json');rows=read('concurrent-frontier-v2','manifest.json');attacks=read('concurrent-frontier-v2','attacks.json');transforms=read('concurrent-frontier-v2','transforms.json')
    perf=read('concurrent-frontier-performance-v2','measurements.json');extra=read('concurrent-frontier-verify-v2','native.json');verify=read('concurrent-frontier-verify-v2','summary.json')
    def median(kernel,k,kind,mode,workers=None):
        a=[x['median_ns'] for x in perf if x['kernel']==kernel and x['k']==k and x['kind']==kind and x['mode']==mode and (workers is None or x['workers']==workers)]
        return statistics.median(a)
    table=[];sizes=[];analyses=[]
    for kernel in ('blend','chain','rolling'):
        for k in (8,32):
            a=[median(kernel,k,'local',mode) for mode in ('scalar','serial','atomic')]
            b=[median(kernel,k,'workers','atomic',w) for w in (1,2,4)]
            table.append(f'| {kernel}{k} | '+ ' | '.join(f'{x:.1f}' for x in a+b)+f' | {a[2]/a[1]:.2f} |')
            sizes.append(f'| {kernel}{k} | '+' | '.join(str(next(x['bytes'] for x in rows if x['kernel']==kernel and x['k']==k and x['mode']==mode and x['opt']=='O3')) for mode in ('scalar','serial','atomic'))+' |')
            fields=[]
            for mode in ('serial','atomic'):
                x=next(x for x in attacks if x['file']==f'{kernel}{k}-{mode}-O3.wasm');fields.append(x)
            analyses.append(f'| {kernel}{k} | {fields[0]["nodes"]} | {fields[0]["median_ms"]:.4f} | {fields[1]["median_ms"]:.4f} | {fields[1]["median_ms"]/fields[0]["median_ms"]:.2f} |')
    mult={w:sum(x['multi_worker_inputs'] for x in correctness['results'] if x['workers']==w) for w in (2,4)}
    rss={kind:[x['maxRSS_kib'] for x in perf if x['kind']==kind] for kind in ('local','workers')}
    md=f'''# 並行演算グラフ：実測と採否

結論：主発明には不採用。Wasmのshared memory/atomicを用いる実装は動いたが、方式既知の解析に対する並行化の追加優位性と、既存のthread/Petri-net難読化から独立した新規性を確認できなかった。解析可能なことだけを不採用理由にしていない。

## 正当性と範囲

- 主36 target（通常Wasm、non-atomic逐次VM、atomic VM × 3kernel × K=8/32 × raw/O3）、回復24本。768入力は8境界値の全3組512＋seed付き乱数256。元・変換・回復・1/2/4workerを合わせて **{correctness['total_calls']:,}呼出し、不一致{correctness['mismatches']}**。比較に使う元関数の繰返し呼出しもこの数に含む。
- atomicの複数worker条件は12binary×768入力ずつ。演算を2人以上が取得した入力は2workerで **{mult[2]:,}/9,216**、4workerで **{mult[4]:,}/9,216**。別workerの担当があった証拠であり、CPU命令が同時刻に動いたことの計測ではない。
- 個別命令、引数だけ、定数だけ、ゼロ初期local、引数再代入、16引数の追加 **{verify['extra_targets']} target**：**{extra['total_calls']:,}呼出し、不一致{extra['mismatches']}**。うち4workerを各48入力で実行。
- WABT wasm-interpへowned shared memoryと呼出しwrapperを付けた60本、**{verify['wabt_checks']}呼出し一致**。ここは単一thread実行。別engineでの並行実行は未検査。
- 元にmemory、division、loop、importを含む4例を拒否。回復器は変更runtimeと循環dataも拒否。依存待ちを除去した誤変換は、rootを先に実行すると **{extra['negative']['differences']}/{extra['negative']['inputs']}入力**で不一致。
- SCの2演算・2workerモデルは正しい公開順で結果24のみ、READYを先に公開する誤方式では0の反例。これは小モデルであり、生成Wasm全体の全interleaving検証ではない。

元にtrap、I/O、memory副作用を含むプログラムは非対応。変換後は1page共有memoryとhost adapterが必要。元binaryのAPIをそのまま保つ変換ではない。全入力・全環境の数学的同値性を主張しない。

## 性能

各条件3 fresh Node process、実行順seed付きshuffle、各process7標本。表はprocess内中央値のさらに中央値、単位ns/呼出し。local列は**同じWasm内部loop**、warmup 2048、512反復。worker列はpool生成後のhost同期を含む完了時間、warmup16、32反復。二種は計測境界が異なる。pool構築時間もrawに保存し、ここに含めない。性能測定中に別の重い実験は並行させていない。

| workload | 通常local | 逐次VM local | atomic VM local | 1worker host込 | 2worker host込 | 4worker host込 | atomic/逐次VM local |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

合計108 process。各標本値と3 process間のばらつきはmeasurements.jsonに保存。CPU affinity、周波数、V8 JIT tierは固定していない。短いkernelであり、重いアプリ全体の並列速度を評価したものではない。ownerの記録も両VMに含まれる。

全VMでWasm memoryは65,536 bytes、host barrierは追加8 bytes。通常Wasmはlinear memoryなし。whole Node processのmaxRSSはlocal条件で{min(rss['local']):,}〜{max(rss['local']):,} KiB、worker条件で{min(rss['workers']):,}〜{max(rss['workers']):,} KiB。workerが参照するmemoryは共有であり、worker数だけpageを複製してはいない。RSS差はVMのデータ領域だけの差ではない。

| workload | 通常O3 bytes | 逐次VM O3 bytes | atomic VM O3 bytes |
|---|---:|---:|---:|
{chr(10).join(sizes)}

変換時間（validate/disassemble/compile/validateの外部process込み、12回）中央値{statistics.median(x['elapsed_ms'] for x in transforms):.2f} ms、範囲{min(x['elapsed_ms'] for x in transforms):.2f}〜{max(x['elapsed_ms'] for x in transforms):.2f} ms。再利用ライブラリ・実行環境はenvironment.jsonとsource snapshotを参照。

## 回復費用とアブレーション

全24条件を通常Wasmへ回復し、元のSSA式と構造hashが一致。原本は回復後の評価にのみ使用。回復器の入力は対象binaryと公開runtime仕様。専用の4種類のruntime fingerprint以外は未対応であり、一般逆コンパイラの成功率とはいえない。プロファイル作成の一回限りのtool起動を以下の解析時間に含めない。

| workload | node数 | 逐次VM解析ms | atomic VM解析ms | atomic/逐次VM |
|---|---:|---:|---:|---:|
{chr(10).join(analyses)}

解析は1 warmup＋9回、PythonのNode interningを各回空にする。読み込み・profile照合・初期memory復元・循環検査・topological展開を含み、回復Wasmの外部コンパイルは除く。外部コンパイル込みのtotal_msもattacks.jsonにある。worker数はbinary内の依存グラフを変えないため、同じgraph回復で1/2/4workerすべてを除去できる。通常O3でatomic命令が残る事実は、この回復への耐性を意味しない。

non-atomic逐次VMは演算data・node配置・走査を同一にし、atomic取得とメモリ操作だけを通常操作に置換した対照。atomicを1workerで動かす対照と複数workerを比較することで同期と並行化を分離した。公開thread難読化ツールの再実装や同cost最適化を完了したとは主張しない。

## 失敗・修正と今後の制約

主v1のhost barrierに2回loadによる取りこぼし待ちを発見。正当性は完了したが、v2で単一loadへ修正し、101,376呼出しを再実行した。mainのWasm bytesは変わらない。性能v1はwrapperのparser用module囲いを忘れて測定前に失敗、v2で修正。verify v1の循環反例はpadding不整合で先に拒否されたため、v2でpaddingも修正し循環の拒否理由を検査。いずれも解析耐性に数えない。

本案は「合法な一つの実行順に固定してよい」点を解決しない。worker数やnodeのランダム配置を増やすだけの再設計は行わない。別案には、実行に必要な依存が公然と列挙される構成を超える具体的な機構と、その機構の追加効果が必要。これは今後の条件であり、まだ発明済みの方式ではない。特許目標と新規な主方式の確立は未達。
'''
    (HERE/'analysis.md').write_text(md,encoding='utf-8');print(json.dumps(dict(multi=mult,extra_calls=extra['total_calls'],negative=extra['negative'])))

if __name__=='__main__':main()
