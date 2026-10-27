# -*- coding: utf-8 -*-
"""Produce the report from recorded measurements, retaining initial diagnostics."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'results/invention-20261019'
def read(folder,name):return json.loads((BASE/folder/name).read_text(encoding='utf-8'))

main=read('nilpotent-stencil-v1','summary.json')
batch=read('nilpotent-stencil-batch-v1','summary.json')
attacks=read('nilpotent-stencil-v1','attacks.json')
transforms=read('nilpotent-stencil-v1','transforms.json')
rows=[]
for b in batch:
    if 'kind' in b and b['mode']!='dynamic':continue
    original=next(r for r in main if r['path']==b['path'])
    baseline=next(r for r in batch if r['model']==b['model'] and r['mode']=='source')
    mode=b['mode']+(' recovered' if 'kind' in b else '')
    rows.append('| %s | %s | %s | %.3f [%.3f, %.3f] | %.2f | %.2f |'%(b['model'],mode,original['bytes'],b['median_ns'],*b['range_ns'],b['median_ns']/baseline['median_ns'],b['median_rss_KiB']/1024))
arows=['| %s | %s | %.4f | %s | %s | %.2f |'%(r['model'],r['mode'],r['median_ms'],r['vector_memo'],r['valuation_products'],r['total_ms']) for r in attacks if r['opt']=='O3']
tt=[r['transform_ms'] for r in transforms]
text='''# 4点実行：実測と反証

2026-10-19。元式を4つのずらした入力で評価し、32bit環で高次項が消える条件から出力を合成するWasm変換を実装した。dynamic版の各lane入力写像は非単射で、通常O3後もSIMD評価が残る。しかし、方式を知る解析者は入力を逆算せず、定数係数を追って30/30条件をscalarへ回復できた。独立した新規性と十分な追加保護優位性は確立できず、主発明には不採用とする。

## 比較と正当性

5つの小さいpure polynomial kernel。cubic、quartic、bivar、反復4/8段のiter4/iter8であり、5個の実アプリではない。iter8は構文上の多項式次数256で、関数としての最小表現次数を測定したわけではない。source/diagonal/constant/dynamicの4方式×raw/O3で40本、回復30本、計70本。diagonalはSIMD化だけ、constantは固定方向の4点合成、dynamicは非単射の入力写像を用いる。

- 主70本×4,288入力=300,160呼出し、不一致0。境界64、walking bit128、seed固定乱数4,096を含む。
- 異なるランダム式12モデルの60本で257,280呼出し、不一致0。主と合わせ130本・557,440呼出し。再実行を独立カバレッジに加算しない。
- Python整数参照値とWABT interpreterによる主70本×6=420呼出し、不一致0。
- 回復30本と元binaryから抽出したscalar式について、Z3 4.13.3の32bit同値性問い合わせが30 unsat、sat/unknown各0。SIMD変換器・parser・compilerを含む全体の機械証明ではない。
- reduced widthおよび32bitで16,000組の単項式・方向を検査。全入力を列挙したものではない。
- sourceの除算・XOR・捨てられるtrap、および誤ったshift・出力重み・vector XORの計6件を拒否。後者3件の実Wasm反例は0→2,147,483,648、1→3,074、1,024→3,072だった。
- 各lane入力の非単射性は、異なる2入力が同じ値になる4組を実Wasmで確認した。これは全プログラムの解析困難性を意味しない。
- 条件を緩めても正しくなる正の対照として、3次式のshift=0と偶数係数4次式のshift=7を回復した。追加6本・25,728呼出しで一致。解析器が固定shift=8の構文だけを認識しているわけではない。この件数は上記130本の外数。

対象にはmemoryや公開副作用がなく、許可した演算はtrapしない。任意のmemory副作用・trapを保存できるという結果に拡張しない。WABTとNodeのvalidationを使用した。

## 実行費用

Windows10.0.26100、Intel i9-11900K @3.50GHz、Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。CPU affinity・周波数は固定しない。

最初のv1はJS境界を含む210 fresh processを測ったが、入力変換・呼出し側のJIT等によるばらつきが大きかった。その値を速度優位の主張に使わず、同一のWasm内部loopを各O3 binaryに加えたbatch-v1を主値とする。元/変換/全回復の35条件×3 fresh process=105 process。条件順は固定seedで混ぜ、逐次実行した。

各processで1,000,000 kernel呼出しをwarmupし、11標本×200,000呼出しを測る。表は3processの中央値の中央値と、process中央値の最小・最大。信頼区間ではない。loop、入力更新、rolling checksumの費用を含み、純粋な単一命令時間ではない。harnessは700検査と7,140回の参照呼出しで照合した。

|kernel|方式（O3）|元binary byte|ns/iteration [範囲]|source比|process RSS MiB|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

recoveredはO3後の変換物から回復したものに追加O3をかけていない。binaryサイズは測定harnessを付加する前。全条件のlinear memoryは0page、GC allocationもないが、Wasm/Node/JIT自体のメモリ使用量0という意味ではない。RSSはprocess全体のhigh-water mark。実アプリ・別機器への速度一般化は行わない。

## 解析・変換費用

各バイナリを読み込んだ後、付値と定数係数の射影を9回測定。表の解析msは中央値、全回復msはvalidation・read・compileを含む単回値。

|kernel|方式|射影中央値ms|vector memo節点|付値積の組合せ|全回復ms（単回）|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(arows)+f'''

15変換の単回時間は{min(tt):.2f}〜{max(tt):.2f}ms。外部tool起動を含むため小さい差の有意性を主張しない。解析器の開発費用・人の解析時間は測定していない。NotDec/StackSight本体は実行していない。主解析では未対応・crash・timeout・誤答は0で、全30条件がrecoveredである。

## 何が分かったか

前案の「最後に一つのlaneを取り出す」という弱点には対処している。4点の出力が合成に必要で、各入力写像の逆関数も一般には存在しない。それでも公開命令からkの定数係数を伝播すれば元のDAGが戻る。生成時に高次項を消す条件が、解析時にも保持すべき係数を最大4個に制限しているためである。高次数や非単射性による困難性を期待した仮説は支持されない。

動的版の解析費用増は存在する。しかしconstant対照に対して大きな非局所の探索を強制せず、実行側ではsourceの約4〜6倍の反復時間を要した。Python解析時間とV8実行時間を直接割って保護効率にしない。回復可能という事実だけで不採用にせず、安い射影の構成、実測した増分、[近接する自己還元・符号化計算](prior-art.md)との技術差を合わせて判断した。

初期probe-v1は記録用dictのmode重複というrunner bugで中断した。修正後のprobe-v2と主v1の70binaryは全てbyte一致。初期失敗を保護効果や意味不一致へ加算しない。主実装の修正・主要な設計変更は行っていない。

## 保存結果

[主manifest](../../results/invention-20261019/nilpotent-stencil-v1/manifest.json)、[主正当性](../../results/invention-20261019/nilpotent-stencil-v1/correctness.json)、[解析全標本](../../results/invention-20261019/nilpotent-stencil-v1/attacks.json)、[batch性能全標本](../../results/invention-20261019/nilpotent-stencil-batch-v1/benchmark.json)、[追加検査](../../results/invention-20261019/nilpotent-stencil-verify-v1/random/correctness.json)、[誤変換の反例](../../results/invention-20261019/nilpotent-stencil-verify-v1/counterexamples.json)、[SMT結果](../../results/invention-20261019/nilpotent-stencil-proof-v1/proof.json)、[byte再現](../../results/invention-20261019/nilpotent-stencil-v1/replay.json)。新規で有効な主発明・特許性の確立は未達である。
'''
(HERE/'analysis.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(runtime_rows=len(rows),attack_rows=len(arows))))
