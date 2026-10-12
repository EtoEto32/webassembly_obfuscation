"""Integrate complete hash evaluation of one public seed, not a claimed obfuscation effect."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/runtime-mining/cross-dataset/swamped'
r = json.loads((OUT/'046dc081-repeated-throughput.json').read_text())
assert r.get('finished_utc') and r['status']=='all public vectors matched'
assert len(r['results'])==5 and all(v['matches'] for v in r['results'])
assert len(r['benchmark']['samples'])==3 and all(s['final_output_matches'] for s in r['benchmark']['samples'])
assert r['script_sha256']==hashlib.sha256((ROOT/'experiments/runtime-reference/swamped-seed-check.cjs').read_bytes()).hexdigest()
rates = [s['hashes_per_second'] for s in r['benchmark']['samples']]
summary = dict(sha256=r['sha256'],median_hps=statistics.median(rates),min_hps=min(rates),max_hps=max(rates),
               vectors_matched=5,repetitions=3,seconds_per_block=30,warmup_seconds=3,
               role='published input seed; not a paired obfuscation result',
               host='recovered Emscripten ABI; original generated JS unavailable',
               report='046dc081-repeated-throughput.json')
(OUT/'046dc081-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
p = ROOT/'paper/main.tex'; text=p.read_text(encoding='utf-8')
if '\\label{sec:swamped-hash}' not in text:
    section = r'''\subsection{SWAMPEDの公開入力標本での完全なハッシュ計算}
\label{sec:swamped-hash}
SWAMPEDのCryptojackers\_43にある取得済み42標本を調べ，ハッシュ関数のexportとホスト依存性を照合した．うちSHA-256が\texttt{046dc081}で始まる標本について，\texttt{\_cryptonight\_create}と\texttt{\_cryptonight\_hash\_variant\_0}を呼び出した．元のJavaScriptが付属しないため，Wasmのimportと命令列に基づいて旧Emscriptenのメモリ・表・時刻・UTC変換・プロセスIDを提供した．必要な処理を空の関数へ置き換えず，未対応のホスト呼出しはエラーにする．初期メモリは16 MiBで，ホスト側の配置は元JavaScriptと同一であるとは主張しない．計算後の出力はXMRigの公表v0入力5件すべてと一致した．

同じ隔離ランタイムで，1 worker，3秒のウォームアップ，30秒以上の3反復を行った．中央値はMEDIAN H/s，最小MINIMUM H/s，最大MAXIMUM H/sで，全反復の最終ハッシュ出力も一致した．この標本は公開の変換入力であり，同一条件の難読化版との対応はまだ構成していないため，難読化のオーバーヘッドを示す結果には含めない．既報のimportを空にした実行時間とは，ハッシュを最後まで計算して期待値を確認した点が異なる．ただし既報の測定条件とは一致せず，両者の数値を直接比べない．取得記録全体でSHA-256を照合すると，この入力はMinerRay，WasmBench，WASMixer，WasmMalにも同じバイナリとして収録されていた．初期の採掘候補一覧だけを用いた照合ではこの重複を見落としていたため，全取得記録との照合へ改めた．同じ標本の再収録を独立した実装とは数えず，本稿の追加評価は完全な出力検証と自生成変換対の比較という対象・条件で位置付ける．

'''
    section=section.replace('MEDIAN',f'{summary["median_hps"]:.2f}').replace('MINIMUM',f'{min(rates):.2f}').replace('MAXIMUM',f'{max(rates):.2f}')
    text=text.replace('\\section{考察}',section+'\\section{考察}',1)
p.write_text(text,encoding='utf-8')
draft=ROOT/'experiments/runtime-reference/csec-submission-draft.txt'
s=draft.read_text(encoding='utf-8')
if 'SWAMPED追加実測：' not in s:
    s += f'\nSWAMPED追加実測：公開入力標本046dc081…のCN/0出力5件が一致．30秒以上・3反復の中央値{summary["median_hps"]:.2f} H/s．復元したホストABIで測定し，同一条件の難読化版との比較は未完了．\n'
draft.write_text(s,encoding='utf-8')
print(json.dumps(summary,indent=2))
