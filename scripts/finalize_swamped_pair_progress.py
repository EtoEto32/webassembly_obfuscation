"""Save actual new progress without declaring the broad research goal complete."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
OUT=BASE/'swamped'
rows=json.loads((OUT/'controlled-pair-summary.json').read_text())
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
ja='''公開WebAssembly採掘データセットの難読化について，配布設定と実際の機構を照合し，ハッシュ出力の正しさと計算速度を評価する．通常の処理と研究用計測を対照に，代表例の平坦化，仮想化，算術式置換，間接呼出しを確認した．既存のCryptic Bytesの静的解析に加え，Proof-of-Theftの2つの配布実装とSWAMPEDの入力標本を公表テストベクトルで照合した．xmr-wasmでは分岐表を使わない状態による平坦化を確認し，30秒以上・3反復の速度中央値は基準9.11 H/sに対し平坦化版6.18 H/sであった．ただし配布設定の不一致や最適化の交絡がある標本は，手法の効果とは解釈しない．SWAMPED入力に同じ組立条件でnop挿入と整数定数分割を適用した対照では，命令数が1.097倍と1.034倍，速度中央値比が0.960と0.973で，反復の範囲は重なった．静的な増加だけでは速度低下を確定できず，機構の適用範囲と測定条件を区別する必要がある．追加実測は外部プールに接続せず，報酬を発生させないローカル環境で行った．有限の入力と標本に関する結果であり，全公開標本の網羅や検出回避能力は主張しない．'''
en='''We analyze obfuscation mechanisms and validated hashing performance in public WebAssembly mining datasets, distinguishing declared settings, observed mechanisms, normal processing, and research instrumentation. Beyond prior static analysis of Cryptic Bytes, we check public hash vectors in two distributed Proof-of-Theft implementations and a SWAMPED input artifact. The flattened xmr-wasm wrapper uses state-based dispatch without a branch table; repeated 30-second measurements yield median rates of 9.11 hashes/s for the reference and 6.18 hashes/s for flattening. Build-label discrepancies and optimization differences limit causal interpretations of other artifacts. In a controlled SWAMPED comparison, locally generated NOP insertion and integer constant splitting increase instruction counts by factors of 1.097 and 1.034, while median throughput ratios are 0.960 and 0.973 with overlapping observed ranges. Static growth alone does not establish throughput loss. Additional experiments run locally without external pools or mining rewards. Findings are limited to the evaluated inputs, artifacts, and conditions; we do not claim complete coverage or detector-evasion effectiveness.'''
s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:'\\begin{abstract}\n'+ja+'\n\\end{abstract}',s,count=1,flags=re.S)
s=re.sub(r'\\begin\{eabstract\}.*?\\end\{eabstract\}',lambda m:'\\begin{eabstract}\n'+en+'\n\\end{eabstract}',s,count=1,flags=re.S)
s=s.replace('Wasmエンジンによる最適化の関与は考えられるが，', '反復の最小・最大の範囲は3標本で重なり，この3反復から小さな中央値差を確定的な性能低下とは扱わない．また，挿入nopを除去し，分割式を剰余演算で元の定数へ戻すと，モジュール全体のWAT命令列が基準版と完全一致することを確認した．Wasmエンジンによる最適化の関与は考えられるが，')
p.write_text(s,encoding='utf-8')
draft=ROOT/'experiments/runtime-reference/csec-submission-draft.txt';t=draft.read_text(encoding='utf-8')
if '同条件のSWAMPED変換対：' not in t:t+='\n同条件のSWAMPED変換対：元配布とSHAが一致する再組立基準に対し，公開変換コードからnop/整数定数分割を自生成．全3標本の公表ハッシュ5件と全9測定ブロックの出力が一致．各30秒以上・3反復，基準32.39 H/s，nop31.08，定数分割31.53．反復範囲が重なり，小差を確定効果としない．自生成変換版と公開配布標本は区別する．外部プールへ接続しない．\n'
draft.write_text(t,encoding='utf-8')
coverage=BASE/'verified-execution-coverage.json';c=json.loads(coverage.read_text())
for r in rows[1:]:
    if not any(m['sha256']==r['sha256'] for m in c['modules']):
        c['modules'].append(dict(sha256=r['sha256'],dataset='SWAMPED-derived local transformation',
             role='locally generated counterpart, not a public released transformed binary',
             runtime_report='swamped/controlled-pair-repeated-throughput.json',
             mechanism_report='swamped/controlled-pair-mechanism-audit.json',correct_public_vectors=5,
             seconds_per_block=30,repetitions=3,causal_generalization_established=False))
c['public_and_locally_generated_unique_checked_repeated_modules']=len(c['modules'])
c['new_controlled_comparison']='swamped/controlled-pair-manifest.json'
c['unresolved']=[u for u in c['unresolved'] if u!='SWAMPED obfuscation pair']
c['unresolved'].append('additional SWAMPED seeds, techniques and random realizations beyond this one controlled pair')
coverage.write_text(json.dumps(c,indent=2)+'\n')
note='''
追加進捗：SWAMPEDの同条件変換対を完成。prepare_swamped_controlled_pair.pyで浮動定数を含むvariant_2だけ整数分割から除外し，nop30関数3089箇所，整数分割29関数542箇所を自生成。基準の再組立SHAは元配布と完全一致。公開関数本体を保持し，位置選択beta(1,1)をseed固定へ変更した適応をmanifestに明記。
controlled-pair-public-vector-check.jsonで3標本×5入力全一致。exec68458とDocker swamped-pair-repeated-20261008はexit0で完了。controlled-pair-repeated-throughput.jsonは全9ブロック完了，各30秒以上，3秒warmup，1worker，実行順回転，context初期時刻固定，全最終出力・測定後5入力全一致。基準32.39 H/s（27.09--32.73），nop31.08（29.56--32.72），定数分割31.53（28.94--32.08）。速度比0.960/0.973，命令比1.097/1.034。範囲重複，確定的な速度低下・高速化を主張しない。
controlled-pair-mechanism-audit.jsonは挿入nop除去/整数式回復で全WATが元と完全一致する確認。全入力runtime意味保存の証明とは区別。
集計scripts/summarize_swamped_controlled_pair.py，原稿反映integrate_swamped_controlled_pair.py，仕組みaudit_swamped_controlled_mechanisms.py。図controlled-pair-throughput.pdf/png，summary.csv/json，3static.json保存。元配布/自生成を区別。paper/main.texのRQ2構成と要旨も更新，追加実測は全てnetworknone。ゴール全体は未完了，元配布難読化版の統一ビルド，ハッシュ本体のPoT機構範囲，追加公開標本と元PDF対照との統合，原稿の圧縮とPDF点検を続ける。利用枠20%使用・80%残確認。内蔵コンパイラの環境エラーは継続。
'''
with (BASE/'proof-of-theft/resume-state.txt').open('a',encoding='utf-8') as f:f.write(note)
print('Saved controlled comparison, refreshed abstracts, coverage and remaining full scope')
