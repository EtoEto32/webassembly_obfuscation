# -*- coding: utf-8 -*-
import argparse,json,statistics
from pathlib import Path
def read(d,n):return json.loads((Path(d)/n).read_text(encoding='utf-8'))
def main(root):
    root=Path(root);base=root/'exception-packet-v3';ver=root/'exception-packet-verify-v1';perf=root/'exception-packet-performance-v1'
    m=read(base,'manifest.json');c=read(base,'correctness.json');a=read(base,'attacks.json');v=read(ver,'summary.json');times={x['file']:x for x in read(ver,'analysis-fresh-pool.json')};pp=read(perf,'summary.json');normal=read(root/'exception-packet-normal-v1','results.json');proof=read(ver,'scalar-model-equivalence.json')['proofs']
    supported={x['file'] for x in proof if x['status']=='unsat'}|{x['file'] for x in normal if x['equal']}
    lines=['# 例外参照packet：実測と判定','', '2026-10-19。主方式には不採用。共有による例外生成費用の削減はあるが、二タグの意味を通常selectへ戻す解析に対する優位性は得られなかった。独立した新規性・特許性は未確立。','',
      '## 主検査','',f"3カーネル×4/16/48選択×4方式×raw/O3の72 targetと、復元72本。各1,024入力（境界8値の3引数全組合せ512＋固定seed乱数512）、計{c['calls']:,}呼出し。不一致{c['mismatches']}、予期しない例外{c['unexpected_exceptions']}。同じinstanceを継続利用。plain18、helper18、packet36であり、72を全て保護版とは数えない。",
      '',f"適応的回復は{sum(x['status']=='recovered' for x in a)}/72、うちpacket36/36。raw36条件は元と同じ構文DAGへ戻り、O3は演算順等が異なるので一致を強制しない。WABT interpreter {v['interpreter_calls']}呼出しも一致。SMTのscalarモデル比較は{v['unsat']}/72がunsat、4が10秒上限のunknown。別の交換・結合則による正規化は60/72で一致し、4つのunknownを全て含む。両検査の和集合は{len(supported)}/72。ただしEHを含むバイナリ全体の機械検証ではない。",
      '', '入力引数を書き換える例、非正規化条件、select結果を次条件にする例の12 target＋復元12本は、元の再実行込み24,864呼出しで不一致0。誤handler版は518/518入力で不一致、null packet版は518/518でtrap。memory/import/loop/divisionの4拒否対照も保存した。',
      '', '## 実行・サイズ・解析の比較','', 'O3。時間は各3 fresh processの中央値の中央値。実行は共通Wasm内部loopを追加し、追加後は最適化しない。warmup 2,048回、512呼出し×9標本。入力とchecksumを毎回更新する。解析はBinaryenでの読取りを除き、global式intern poolを毎回空にして関数summaryと結果式を再構築。1回warmup後9標本の中央値。',
      '', '|kernel / K|方式|bytes|実行 ns/回|process中央値の範囲 ns|解析 ms|解析step|', '|---|---|---:|---:|---:|---:|---:|']
    for f in pp['files']:
        t=times[f['file']];lines.append(f"|{f['kernel']} / {f['k']}|{f['mode']}|{f['bytes']}|{f['median_ns']:.1f}|{f['min_ns']:.1f}–{f['max_ns']:.1f}|{t['median_ms']:.3f}|{t['steps']}|")
    tx=read(base,'transforms.json');rss=[y for x in pp['files'] for y in x['maxRSS_KiB']]
    lines += ['',f"全{pp['fresh_processes']} processを固定seedで順序shuffleし逐次測定。各processで4種のiteration数のharnessを独立JS oracleへ照合し計432 check一致。CPU/OS/Node/V8は主結果environment.json。CPU affinity・周波数・JIT tierは固定せず、単一CPUの小カーネル実験。標本数が短いplainの数ns差は性能優位としない。",'',
      f"追加linear memoryは全方式0。process maxRSSは{min(rss):,}–{max(rss):,} KiBでNode/V8等を含む。例外heapの厳密な割当てbyte量やpeak live object数は未測定。変換36件は{min(x['elapsed_ms'] for x in tx):.1f}–{max(x['elapsed_ms'] for x in tx):.1f} ms（validate/disassemble/compile子process起動を含む、各1回）。",'',
      'K=48のfresh→sharedはblend約71.4→6.0µs、chain約75.7→6.1µs、rolling約71.1→10.7µs。共有は有益な実行最適化だが、helperの約74/69/75nsに対してまだ約81/89/143倍。解析の追加費用は約2.5/2.9/3.5倍で、こちらも共有によって軽くなり得る。絶対比の単純比較を一般的な保護スコアとせず、今回の安い二タグsummaryが残る事実と合わせて不採用とした。', '',
      '## 失敗・未対応を耐性と混同しない','',
      '- 予備回復器は参照仮引数を扱えなかった。二タグdomainのsummaryを実装して解決した。',
      '- 主v1はDAGを木として繰り返し歩く実装不備があり、自分の実行を中断。v2でinterningと既訪問検査を加えた。',
      '- v2の24件は回復後の確認器のlocal数上限128を超えた。回復自体は出力済みで、上限を4,096へ広げたv3では72件全て実行照合できた。変換効果とは数えない。',
      '- GCを含む全機能を有効にしたO3出力3本はWABTが非null参照のblock署名を読めない。V8ではvalid、Binaryen経由で3/3回復し値も一致。主実験は必要なEH/reference-typesだけを有効にしたO3。互換性失敗を耐性としない。',
      '- タグ宣言と関数順を反転した3本も回復。上記3本と合わせ9,216呼出しで不一致0。特定fixture名や添付正解表による照合ではない。',
      '- 補助SMTの4件はunknownのまま履歴を保存した。条件を4領域へ分ける追加SMTも一部unknownで、成功扱いにしない。交換・結合則の整理が有効だった。モデルの同値性検査とEH回復費用は別の測定である。','',
      '## 結論と次の制約','',
      'VM管理の参照であっても、その生成・利用が公開され、観測する情報が二つのtagだけなら、小さな意味domainへ写せる。共有するidentityが出力に影響しないので、オブジェクトの生成履歴を復元せずに解除できた。再送回数・handler数・タグ名を増やすだけの改良は試さない。次候補には、保護対象の計算を再構成する際に、このような小さな局所summaryでは捨てられない具体的な関係が必要である。これは設計上の制約であって、一般の例外難読化の不可能性の証明ではない。','',
      '一次結果：`results/invention-20261019/exception-packet-v3/`、`exception-packet-performance-v1/`、`exception-packet-verify-v1/`、`exception-packet-compatibility-v1/`、`exception-packet-normal-v1/`。再現は[README](README.md)、設計は[algorithm](algorithm.md)、先行技術は[prior-art](prior-art.md)。']
    Path(__file__).with_name('analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('results');v=a.parse_args();main(v.results)
