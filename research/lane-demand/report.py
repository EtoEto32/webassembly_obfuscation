# -*- coding: utf-8 -*-
import json
from pathlib import Path
import statistics
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'results/invention-20261019'
def read(folder,name):return json.loads((BASE/folder/name).read_text(encoding='utf-8'))
def main():
    summary=read('lane-demand-v3','summary.json');bench=read('lane-demand-v3','benchmark.json');attacks=read('lane-demand-v3','attacks.json');transforms=read('lane-demand-v3','transforms.json')
    rows=[]
    for r in summary:
        if r['opt']!='O3' or ('kind' in r and r['mode']!='dynamic'):continue
        rss=statistics.median([b['maxRSS_KiB']/1024 for b in bench if b['path']==r['path']]);source=next(s for s in summary if s['model']==r['model'] and s['mode']=='source' and s['opt']=='O3')
        mode=r['mode']+(' recovered' if 'kind' in r else '')
        rows.append('| {} | {} | {} | {:.2f} [{:.2f}, {:.2f}] | {:.2f} | {:.2f} |'.format(r['model'],mode,r['bytes'],r['median_ns'],*r['range_ns'],r['median_ns']/source['median_ns'],rss))
    arows=[]
    for r in attacks:
        if r['opt']!='O3':continue
        arows.append('| {} | {} | {:.4f} | {} | {} | {:.2f} |'.format(r['model'],r['mode'],r['median_scalarize_ms'],r['demand_visits'],r['memo_entries'],r['total_ms']))
    text='''# 入力依存レーン移送：実験結果

2026-10-19。動的なレーン移送はBinaryen O3後にも残るが、今回の方式既知の需要解析では24/24条件をscalar式へ戻せた。動的版の解析費用は固定frame版より増えたものの、複雑なframeを解く必要はなく、生成規則から1レーン需要へ閉じる。独立した新規性・十分な追加効果を確立しておらず、主発明には採用しない。回復可能という事実だけを不採用理由にしない。

## 実験の範囲

diamondは分岐した式の合流を持つ小さい整数kernel、mix1/4/8は定数乗算・rotate・加算・XORを1/4/8段行う同族kernel。4個の独立した実アプリではない。各々source/vector/static/dynamic、raw/O3の32条件、3変換方式×4式×2最適化の回復24本、計56binary。sourceはscalar、vectorはframeを0固定、staticは節点ごとの定数frame、dynamicは入力依存frameである。余分な計算・固定移送・動的移送を段階的に比較するアブレーションになっている。

Python3.9、Node24.15.0 / V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Windows10.0.26100、Intel i9-11900K @3.50GHz。CPU affinity・周波数は固定しない。外部ネットワークや課金は実験に不要。

## 正当性

- 主56binaryで各4,288入力、合計240,128呼出し、不一致0。境界64、walking bit128、seed固定乱数4,096。
- 独立のPython参照値とWABT interpreterを主56本×6入力、合計336呼出しで比較。不一致0。
- 異なる式・seedの追加12モデルで、source/raw/O3/回復の計60binary、257,280呼出し、不一致0。元4kernelだけに一致する検査ではない。
- 主・追加を合わせ497,408呼出し。再実行を別カバレッジとして数えない。全方式にmemory、GC allocation、公開副作用はなく、対象演算はtrapしない。memory副作用やtrapの一般保存を検証したという結果ではない。
- 除算、捨てられるtrap計算の2sourceを変換対象外として拒否。word境界を崩すswizzleと範囲外zero化を生むindexの2binaryを回復対象外として拒否。
- 需要indexが0へ消えない手作り対照では、selectを残して正しいscalarへ回復。32入力×元/回復の64呼出しが一致した。indexを常に0と仮定すると24入力で誤る。
- Z3 4.13.3で、**バイナリから抽出したscalarの元式と回復式**の差を問い合わせ、24/24がunsat、sat/unknown各0。32bit入力全域に対するこのモデル内の同値性であり、SIMD出力全体・parser・compilerを含む端から端の機械証明ではない。cursor相殺恒等式もunsat、誤って非零cursorを0とする対照はsat。

## 実行費用

主値はv3。各binaryに3回のfresh Node process、10,000warmup、11標本×10,000呼出しを用いた。計168processを固定seedで並べ替えて逐次実行。表は各processの中央値3値の中央値、角括弧はその最小・最大。信頼区間ではない。JS→Wasm呼出し・引数計算・checksumの費用を含む。

|kernel|方式|byte|ns/呼出し [process中央値の範囲]|source比|RSS中央値 MiB|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

recoveredはO3を適用した変換物からの回復であり、回復後に追加O3をかけた値ではない。全binaryのlinear memoryは0ページ、GC allocationも0。RSSはNode/JIT等を含むprocess high-water mark。小さいkernelでノイズの割合が大きく、広い範囲の標本もあるため実アプリの速度や有意差を断定しない。

## 解析・変換費用

方式既知の解析は元の式、seed、frameの表を読まない。Wasmの命令をDAGへ読み、要求laneの式をmod4で運ぶ。7回の純粋なscalarizationの中央値と、validation・read・compileまで含む単発の全回復を分ける。

|kernel|入力方式|scalarization中央値ms|需要処理回数|memo項目|全回復ms（単発）|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(arows)+'''

'''+ '全変換時間は12条件の単発値で{:.2f}〜{:.2f}ms。外部tool起動・validationを含み、単発の差を統計的な効果とはしない。\n\n'.format(min(r['transform_ms'] for r in transforms),max(r['transform_ms'] for r in transforms))+'''動的frameは構文量とcursor整理の費用を増やす。一方、出力から追うindexは各生成節点のframeへ相殺され、入力依存frameをSMTで解く作業は不要だった。これは「複雑なframe関数を作れば、その逆解析費用を強制できる」という仮説を支持しない。今回のms値はこのPython解析器の実装に依存し、人間解析・NotDec・StackSightの測定ではない。

## 修正履歴と失敗分類

最初のprobeは定数indexのswizzleを未対応と扱った。定数のword循環移送として処理できるように直し、主実験では全24条件を回復した。未対応を保護成功とは数えない。

v1はDAGをtreeへ展開して回復コードを出力し、rotateの共有部分を重複生成していた。v2でDAG共有を保つように修正した。v3では入口validationを明示し、現在の実装を別出力先で実行。v2/v3の全56binaryはbyte一致した。解析器の無駄で大きくなったv1の時間を主効果には使わない。

verify-v1は、非零cursor対照で式parserへmodule wrapperを渡し忘れたため未完了。主24回復ではcursorが0へ消えるのでこの分岐を通らず、対照によって発見された解析器のbugである。修正後verify-v2が完走。クラッシュ/未対応/意味不一致を混同しない。主v3の回復にはunsupported・timeout・crashはなく、全部recovered。既存decompilerの評価は未実施。

## 技術差と結論の範囲

[先行技術](prior-art.md)に、SIMD register/laneのVM、scalar操作のvector化、必要要素による簡約がある。本案の入力依存frame・4つの仮入力という生成規則は記述したが、独立した発明としての新規性は確立できなかった。[設計と補題](algorithm.md)では、frame整合性が解析側にもそのまま使えることを示した。

支持するのは、限定Wasm変換の動作、通常O3への残存、方式既知の解析の有限な費用増加、同じ結果を計算するscalar式の回復、および1レーン需要へ縮む失敗原因である。解析不能性、一般Wasm対応、最良の費用対効果、特許性は主張しない。次の案で必要なのは位置の複雑化だけでなく、出力に必要な複数の値が安く分離・縮約できない具体的な機構である。

## 生データ

[主v3](../../results/invention-20261019/lane-demand-v3/summary.json)、[全性能標本](../../results/invention-20261019/lane-demand-v3/benchmark.json)、[解析](../../results/invention-20261019/lane-demand-v3/attacks.json)、[正当性](../../results/invention-20261019/lane-demand-v3/correctness.json)、[追加検査](../../results/invention-20261019/lane-demand-verify-v2/random/correctness.json)、[対照](../../results/invention-20261019/lane-demand-verify-v2/controls.json)、[SMTと保存query](../../results/invention-20261019/lane-demand-proof-v1/proof.json)、[byte再現](../../results/invention-20261019/lane-demand-v3/replay.json)。verify-v2はv2を用い、v2/v3のbyte一致で主結果に対応する。新規で有効な主発明の確立という研究全体の目標は未達である。
'''
    (HERE/'analysis.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(runtime_rows=len(rows),attack_rows=len(arows))))
if __name__=='__main__':main()
