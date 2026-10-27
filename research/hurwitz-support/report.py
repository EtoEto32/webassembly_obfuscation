# -*- coding: utf-8 -*-
"""Build tables directly from saved measurements, without rerunning them."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;BASE=ROOT/'results/invention-20261019'
def read(folder,file):return json.loads((BASE/folder/file).read_text(encoding='utf-8'))
def main():
    perf=read('hurwitz-support-batch-v1','summary.json');timing=read('hurwitz-support-verify-v1','analysis-timing.json');attacks=read('hurwitz-support-v3','attacks.json');transforms=read('hurwitz-support-v3','transforms.json');correct=read('hurwitz-support-v3','correctness.json');edge=read('hurwitz-support-edge-v1','correctness.json')
    lines=['# 置換列書換えの実測と判定','',
    '2026-10-19。今回の支持制限付きHurwitz書換えは、通常O3後にも表とSIMD計算が残る。しかし、公開binaryの必要な一点だけを追う意味解析で主50/50条件・追加16/16条件を回復した。固定基底変更を超える明確な優位性と独立した新規性は未確立であり、主発明には不採用とする。',
    '', '## 正しさと試験の範囲','',
    f'- 主{correct["binaries"]}本・{correct["calls"]:,}呼出し、不一致0、trap0。source/base/basis/fused/braidのraw/O3が50本、回復と逆書換え後回復が50本。',
    f'- XOR・非定数の反復入力を追加した{edge["binaries"]}本・{edge["calls"]:,}呼出しも一致。主と合計136本・{correct["calls"]+edge["calls"]:,}呼出し。probe・中断v1・再実行v2は追加coverageに数えない。',
    '- 主例の構文上の入力bitは7〜16個、追加例は4個と8個。主比較は4つの非定数例と1つの定数対照。repeated8は生成後の意味解析で定数0と分かったため、非定数保護の成功・失敗件数へ混ぜない。追加active_repeat8は非定数と確認済み。',
    '- 各例について対象bitの全組合せ、およびword境界64組、walking bit128組、乱数2048組を実行。64bit全入力空間をnative実行で列挙したわけではない。',
    '- 主100本についてWABT interpreterの独立エンジンで600呼出しをPython Boolean参照と比較し一致。',
    '- 抽出した元式と回復結果のROBDDから出したcanonical WATが主50条件・追加16条件で完全一致。これは抽出したBooleanモデルの同値性であり、parser・compiler・変換器全体の機械証明ではない。',
    '- S5の全14,400置換対について両方向の積保存28,800検査、変数が重なるランダム因子で8,192検査を実施。',
    '- 共役せず隣接因子を交換する誤変換は、実Wasmでx=1,y=0において0→1の反例を検出。unmasked入力・除算・捨てられるtrap・mutable memoryの4負の対照を拒否。',
    '- v2/v3の主100バイナリはbyte一致。v1はPython再帰処理の不備で中断し、直接再現でもRecursionErrorを確認。明示stackへ修正した後の結果を主値とする。ツール故障を解析耐性に数えていない。',
    '', '## 解析費用','',
    'O3の実binaryからcode/dataを読む時間と、意味解析だけの時間を分けた。下表は読み込み後の5反復の中央値・最小最大。各反復でBDD managerを作り直す。変数順序はbit位置昇順で固定、dynamic reorderingは使わない。主runの単回read/validation時間はattacks.jsonに別記録。',
    '', '|例|方式|意味解析 ms [範囲]|生成BDD node|Apply cache miss|最終Boolean node|','|---|---|---:|---:|---:|---:|']
    for q in timing:lines.append(f'|{q["model"]}|{q["mode"]}|{q["median_ms"]:.3f} [{q["range_ms"][0]:.3f}, {q["range_ms"][1]:.3f}]|{q["bdd_allocated"]}|{q["apply_calls"]}|{q["output_nodes"]}|')
    lines+=['','局所的な逆書換えでは全ての元1bit因子は回復しない。それでも意味解析の前処理として必須ではなく、むしろ追加の費用になった。以下はO3の単回値で、時間差の統計的有意性を主張しない。','',
    '|例|entry数 前→後|降下move数|逆書換えms|その後の意味解析ms|','|---|---:|---:|---:|---:|']
    for q in attacks:
        if q['reduce'] and q['opt']=='O3':lines.append(f'|{q["model"]}|{q["before_entries"]}→{q["after_entries"]}|{q["moves"]}|{q["reduction_ms"]:.2f}|{q["analysis_ms"]:.2f}|')
    lines+=['','主50条件・追加16条件ともunsupported/crash/timeout/resource-limitは0。実装には300,000 node・20秒の上限があるが、これらの条件では達しなかった。v1の実装不備は別記録。NotDec/StackSight本体は今回実行していない。','',
    '## 実行費用','',
    'Windows 10.0.26100、Intel i9-11900K、Python3.9、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。CPU affinity・クロックは固定しない。30 harness×3 fresh processを固定seedで順序を混ぜて逐次実行した。重い検証と同時実行しない。','',
    '全方式で同一Wasm内loopを使い、100,000回warmup後に11標本×10,000回を測定。入力は毎回更新し、結果をrolling checksumへ使用する。値にはloop・更新・checksumを含む。表はprocess中央値の中央値とprocess間の範囲で、信頼区間ではない。数nsの小差を一般的な速度優位と解釈しない。harness自体は600検査・6,120参照呼出しで一致。','',
    '|例|方式 O3|元binary bytes|ns/iteration [範囲]|process RSS MiB|','|---|---|---:|---:|---:|']
    for q in perf:lines.append(f'|{q["model"]}|{q["mode"]}|{q["bytes"]}|{q["median_ns"]:.2f} [{q["range_ns"][0]:.2f}, {q["range_ns"][1]:.2f}]|{q["median_rss_KiB"]/1024:.2f}|')
    lines+=['','元と回復後はlinear memoryなし。変換後は原則1page、repeated16のbraidのみ2page。RSSはNode/JITを含むprocess全体のhigh-water markで、Wasm dataだけのmemory量ではない。binary bytesは測定loop追加前。recoveredはO3変換物から回復し、回復後に追加O3をかけた値ではない。','',
    '## 比較と採否','',
    '|非定数の主例|braid/base 解析時間比|braid/basis 解析時間比|braid/basis 実行時間比|braid/basis binary比|','|---|---:|---:|---:|---:|']
    for name in ['alternating8','mux7','balanced16','repeated16']:
        tt={q['mode']:q for q in timing if q['model']==name};pp={q['mode']:q for q in perf if q['model']==name}
        lines.append(f'|{name}|{tt["braid"]["median_ms"]/tt["base"]["median_ms"]:.2f}|{tt["braid"]["median_ms"]/tt["basis"]["median_ms"]:.2f}|{pp["braid"]["median_ns"]/pp["basis"]["median_ns"]:.2f}|{pp["braid"]["bytes"]/pp["basis"]["bytes"]:.2f}|')
    lines+=['','baseからの有限の解析費用増は認められるが、basisに対しては約0.97〜1.29倍にとどまり、約3倍のbinary拡大を伴う。最大例では既知basisより解析時間・生成nodeが少なかった。実行費用が常に悪化したという結論ではないが、今回の書換えを発明の中核として選ぶほどの追加優位性を示せない。','',
    '表を完全に同費用へ揃えた最適な比較でも、human reverse engineeringの時間計測でもない。native runtimeの改良、さらに大きい入力幅、別の変数順序・他の解析器は未評価。これらの未評価を強度の根拠に使わない。','',
    '## 変換費用','', '|例|方式|因子数|表entry数|変換ms 単回|','|---|---|---:|---:|---:|']
    for q in transforms:lines.append(f'|{q["model"]}|{q["mode"]}|{q["factors"]}|{q["entries"]}|{q["transform_ms"]:.2f}|')
    lines+=['','外部tool起動・validationを含む単回値。entry数には16byteの置換一個を1entryと数える。小さいprefixが抽出時に合成されるため、逆書換え表のentry数とは少し異なり得る。','',
    '## 失敗から得られた条件','',
    '局所的な生成履歴を隠すことと、公開出力へ必要な状態を取り出せないことは異なる。今回、supportの絡みは増え、局所逆変換は止まった。しかし最終観測のためには置換全体でなく5値の状態だけで足り、その意味を正規化すればよかった。次の候補では、逆手順に加えて出力からの小さい状態抽出を最初の反証対象にする。群の幅や書換え回数を増やすだけでは、新しい原理や良い費用対効果を示したことにならない。','',
    '既存のbranch encoding特許と入力依存encoding特許を含む[先行技術照合](prior-art.md)も独立した新規性を弱める。独自で有効な主発明・特許候補の確立は未達であり、研究goalはactive。']
    (HERE/'analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
