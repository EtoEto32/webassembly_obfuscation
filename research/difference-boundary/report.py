# -*- coding: utf-8 -*-
"""Regenerate the measurement note from immutable experiment JSON."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]/'results/invention-20261019'
def read(folder,name):return json.loads((BASE/folder/name).read_text(encoding='utf-8'))
def main():
    perf=read('difference-boundary-batch-v1','summary.json')
    indexed=read('difference-boundary-indexed-v3','results.json')
    transforms=read('difference-boundary-v2','transforms.json')
    lines=['# 差分境界方式の実測と判断','',
    '2026-10-19。境界補正と区間共有による更新の高速化は認める。一方、3つの差分版の配布dataは同じで、元状態は1scanで回復する。固定byte XORに対する保護上の優位性と独立した新規性を確立できず、難読化の主発明には採用しない。',
    '', '## 正当性と範囲','',
    '- 主N=64/1024/8192、追加N=1/2/65536。それぞれ5方式×raw/O3と、その回復物。主60・追加60 target binaryに加え、各targetのmemory観測用版も実行した。',
    '- 各targetにつき21境界ケース＋固定seedの512乱数ケースを同一instanceへ順次適用。主128,040呼出し・9,960 trap、追加128,040呼出し・10,120 trap。合計256,080呼出し、値/trap/対応する表現の全65,536 byteの不一致0。呼出し数はcopyとdigest、通常版と観測用版を合算したもので独立入力数ではない。',
    '- 初期状態と各更新後（trap後も含む）の公開digestと全memoryを照合。元memoryを外部公開した汎用ABIの保存を主張しない。',
    '- 主60 targetをWABT interpreterでも検査し、check export 360呼出し（240正常、120 expected trap）が一致。保存logのtrapはunreachable executed。観測用memoryの全byte比較はNode側で行った。',
    '- N=1..8、各byteが0または255の全状態、全正常コピー区間で112,130モデル比較が一致。共有区間による補正値の一致も検査。全32bit引数・任意byte状態・全runtimeの機械証明ではない。',
    '- 左端補正なし、右端補正なし、copy後に補正を算出、boundsの32bit wrapという4つの誤変換を実Wasm反例で検出。wrap例は双方trapしても、誤版では復号状態が残りdigestが変わる。',
    '- memory公開、digest係数変更、copy後の追加storeの3入力を変換器が拒否。',
    '- main v1/v2の60 binaryがbyte一致。N<8の境界入力生成を一般化した検査器の変更は、生成binaryへ影響しなかった。',
    '', '## 更新・digestの実行時間','',
    'Windows 10.0.26100、Intel Core i9-11900K、Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。CPU affinity・周波数は固定していない。O3 targetへ同じWasm loopを追加し、追加後のwasm-optは行わない。15 harnessを各3 fresh process、固定seedで順番を混ぜて逐次測定。重い検証と同時実行していない。',
    '',
    '各scenario 2,000回warmup、11標本。copyのみは2,000回/標本、digestとpairedは1,000回/標本。全方式の公開digestを戻り値へ使う。digest/pairedでは各回のhashもrolling checksumへ使う。copyのみでも最後に1回digestを計算するため、その費用/反復数を含む。loop・scenario選択・checksumも値に含まれる。',
    '',
    'near=(d=1,s=0,n=N/4)、far=(d=N/2,s=0,n=8)、tail=(d=N-16,s=0,n=16)。pairedはnear後にdigest、digestは状態更新なし。同じ範囲の反復で状態は収束し得るが、scan回数はdata値に依存しない。一般的な実アプリの入力分布とは異なる。以下はprocess中央値の中央値（ns/iteration）。範囲と全生標本は[summary](../../results/invention-20261019/difference-boundary-batch-v1/summary.json)と[benchmark](../../results/invention-20261019/difference-boundary-batch-v1/benchmark.json)。小差の統計的有意性は主張しない。',
    '', '|N|scenario|plain|xor|roundtrip|two|shared|','|---:|---|---:|---:|---:|---:|---:|']
    modes=['plain','xor','roundtrip','two','shared']
    for n in [64,1024,8192]:
        for s in ['near','far','tail','digest','paired']:
            row=[next(q for q in perf if q['dataset']=='n'+str(n) and q['mode']==m and q['scenario']==s) for m in modes]
            lines.append('|'+str(n)+'|'+s+'|'+'|'.join(f'{q["median_ns"]:.2f}' for q in row)+'|')
    lines += ['',
    'N=8192 nearでは全復号版の約5067nsからsharedの約39nsへ短縮した。同Nのfarではtwo約2429nsに対しshared約1249ns。これは共有した読取り量の削減と整合する。一方、farの元copyは約11nsで、sharedはなお約110倍の時間を要する。nearの改善だけを全workloadへ一般化しない。digestを含むとscan費用が支配し、copyの差は薄まる。',
    '', '## サイズ・メモリ・変換時間','',
    '|N|plain bytes|xor|roundtrip|two|shared|','|---:|---:|---:|---:|---:|---:|']
    for n in [64,1024,8192]:
        lines.append('|'+str(n)+'|'+'|'.join(str(next(q['bytes'] for q in perf if q['dataset']=='n'+str(n) and q['mode']==m)) for m in modes)+'|')
    lines += ['',
    'サイズはloop追加前、初期data込み。全方式が1page（64KiB）で追加のlinear memoryなし。RSS中央値はおおむね37MiBで、Node/JITを含むprocess全体のhigh-water値。配列だけの使用量ではない。変換時間は外部toolの起動・validation・profile照合込みの単回値。',
    '', '|N|方式|変換ms|','|---:|---|---:|']
    for q in transforms:lines.append(f'|{q["n"]}|{q["mode"]}|{q["transform_ms"]:.2f}|')
    lines += ['', '## 方式既知の解析','',
    '未変換12を含む60条件、変換条件だけでは48条件を回復した。全て、既に実行検査した元のraw binaryとbyte一致する。unsupported/error/timeout/crashは完成runでは0。これは限定profileに対する攻撃であり、任意の改変Wasmへの一般的逆コンパイラではない。',
    '',
    f'最初のprofile認識では候補を順次再生成していたため、後の候補ほどtool起動が多かった。この差を強度と数えず、零dataの公開profileをNごとに10個あらかじめ生成した索引攻撃を追加。catalog構築は各Nで約264–350msの一回費用。初期memoryの読取り・validationは別に{min(q["read_validate_ms"] for q in indexed["results"]):.1f}–{max(q["read_validate_ms"] for q in indexed["results"]):.1f}ms。下表はcode hash lookup・ファイル読取り・復号の11反復中央値で、バイナリ再出力と事後正解照合を含めない。',
    '', '|N|plain ms|xor|roundtrip|two|shared|','|---:|---:|---:|---:|---:|---:|']
    for n in [1,2,64,1024,8192,65536]:
        lines.append('|'+str(n)+'|'+'|'.join(f'{next(q["median_ms"] for q in indexed["results"] if q["n"]==n and q["matches"][0]["mode"]==m and q["matches"][0]["opt"]=="O3"):.4f}' for m in modes)+'|')
    lines += ['',
    '主N=8192で、復号のみの11反復中央値はbyte XOR約0.360ms、shared約0.418ms。有限の増加は認めるが、どちらもO(N)の一巡で、差分版3種の復元手順・配布dataは同じ。sharedの更新方式を選んでも回復へ新しい探索課題は加わらない。初期plainはデータをそのまま返すためdecode部分がO(1)であり、完全なbyte出力費用を含めた解析全体との混同はしない。',
    '',
    'indexed v1は、零dataを消したcatalogと実binaryとのdata-count section差を誤って照合した実装不備で停止。codeは同じだった。active dataの意味を確認して修正したv2は完走。v3は重複する事後検証を計測の外へ移した結果であり、保護方式の改善ではない。',
    '', '## 判断と残る条件','',
    '今回の肯定的結果は、符号化状態の更新を全復号せず実行できることと、その費用削減。難読化としては復元費用が既知の線形scanに留まり、hash consumerも元byteを逐次現す。更新過程に元の配列全体を置かないことだけでは保護の根拠にならなかった。',
    '',
    '次の候補では、更新則とconsumerの双方に、同じ小さい復元器が残らないかを実装前に検査する。符号化幅・区間数・反復数だけを増やす改良は新原理と数えない。新規で有効な主発明・特許候補の確立は未達、goalはactive。NotDec/StackSight本体、実アプリ、複数host/engine性能、人間の解析時間、完全な特許調査は未実施。']
    (HERE/'analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
