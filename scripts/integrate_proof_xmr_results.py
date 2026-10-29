"""Integrate verified completed measurements; never substitute a plan for results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
rows = json.loads((OUT / 'xmr-repeated-summary.json').read_text())
p = ROOT / 'paper/main.tex'
s = p.read_text(encoding='utf-8')
if '\\label{sec:xmr-runtime}' not in s:
    labels = ['配布基準', '平坦化', '分割（設定名）', '命令置換（設定名）', '偽制御フロー（$-O2$）']
    lines = ['\\hline', '配布名 & H/s中央値 & 最小--最大 & 命令数比 \\\\', '\\hline']
    for label, row in zip(labels, rows):
        lines.append(f"{label} & {row['median_hps']:.2f} & {row['min_hps']:.2f}--{row['max_hps']:.2f} & {row['instruction_ratio']:.3f} " + r'\\')
    lines.append('\\hline')
    section = r'''
\subsection{xmr-wasmの反復測定と機構との対応}
\label{sec:xmr-runtime}
別の配布実装xmr-wasmの5標本を，配布元のJavaScriptから同期的に呼び出した．Node.js v18.20.4，V8 10.2.154.26-node.37，Intel Core i9-11900K上の隔離コンテナを用い，ネットワークを無効にした．各標本で公表入力3件の一致を確認した後，3秒のウォームアップと30秒以上の計算を3反復した．入力を順に循環させ，各反復で標本の実行順をずらした．スレッド数は1とし，実際の経過時間と完了したハッシュ数から速度を求めた．測定終了時の出力とnonceの不変も15ブロックすべてで確認した．表\ref{tab:xmr-runtime}と図\ref{fig:xmr-runtime}はこの完了した測定を示す．3反復の範囲は信頼区間ではなく，ホストの他の負荷を完全には制御していない．
\begin{table}[t]
\centering\small
\caption{xmr-wasm配布標本の実測（各30秒以上，3反復）．命令数比は配布基準に対する値．偽制御フロー版は最適化条件が異なる．}
\label{tab:xmr-runtime}
\begin{tabular}{lrrr}
''' + '\n'.join(lines) + r'''
\end{tabular}
\end{table}
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{../results/runtime-mining/cross-dataset/proof-of-theft/xmr-repeated-throughput.pdf}
\caption{xmr-wasmの反復速度と静的変化．decl.は配布設定が示す名称で，機構の確認とは区別する．偽制御フロー版の速度と縮小には$-O2$の交絡があり，手法の効果を示す値には用いない．}
\label{fig:xmr-runtime}
\end{figure*}
状態による処理選択を確認した平坦化版は，配布基準と比べて命令数1.166倍，サイズ1.170倍，速度中央値比0.678であった．これに対し，命令置換の設定を持つ標本は命令数1.655倍，サイズ1.641倍だが，速度比は0.738であった．従ってこの配布標本比較では，静的な増加量の順序と速度低下の順序は一致しない．ただし置換版の具体的な式と適用関数の確認は未完了であり，増加した全命令が実行されたとは扱わない．平坦化で確認したhashラッパ以外の処理も測定時間に含まれるため，ラッパの変更だけから低下の全量を説明しない．

偽制御フロー版は23.08 H/sで基準の9.11 H/sを上回り，命令数も0.413倍に減少した．しかし同梱Makefileでこの版だけに明示的な\texttt{-O2}があり，コンパイラの最適化による影響を含む．難読化が計算を高速化したとは結論しない．同じ最適化で再生成した対照がない現段階では，値は配布物の観測として示す．webminerpoolhashcnとの絶対速度の差についても，実装，ホスト呼出し，ビルド条件，測定時間が異なるため，難読化手法の優劣には用いない．

'''
    s = s.replace('\\section{考察}', section+'\\section{考察}', 1)
s = s.replace('図中のOriginalは配布基準', '図中のReference dir.は配布基準')
s = s.replace('本研究では，これらの検出性能を評価し直すのではなく，公開ファイルを実行せずに調べて何が確認できるかを整理する．', '本研究では，これらの公開ファイルの難読化機構を照合し，ハッシュ計算を最後まで実行した出力と速度を追加評価する．')
s = s.replace('難読化の仕組みを確認したのは，目的に合わせて選んだcn-0の一部の箇所である．', '難読化の仕組みを確認したのは，目的に合わせて選んだcn-0の一部とxmr-wasmの公開hash関数である．')
s = s.replace('出力を照合した13件以外の入力と，独立した参照実装や公表テストベクトルによる検証が必要である．', 'プールで受理された13件に加え公表テストベクトルも照合したが，対象入力は有限であり，全入力の正しさを保証しない．')
s = s.replace('長時間の反復，独立した実装への拡張，ビルド条件をそろえた対照は未完了である．', 'xmr-wasmへの拡張と30秒以上の3反復は完了したが，長時間の追加反復，実装間の独立性の確認，ビルド条件をそろえた対照は未完了である．')
s = s.replace('Proof-of-Theftでは設定の構成を，収集されたファイルではコードの特徴の割合を調べ，別の範囲の情報を補っている．', 'Proof-of-Theftでは設定と機構を照合し，2つの配布実装で出力と速度を実測した．収集されたファイルではコードの特徴の割合を調べ，別の範囲の情報を補っている．')
s = s.replace('同標本の短時間反復測定を行い，静的な増加量と計算速度を比較した．', 'xmr-wasmの30秒以上・3反復では，基準の中央値9.11 H/sに対し平坦化版は6.18 H/sであり，静的な増加量の順位と速度低下の順位は一致しなかった．')
s = s.replace('Long-duration evaluation and build-condition auditing remain in progress.', 'Repeated 30-second xmr-wasm measurements yielded median rates of 9.11 hashes/s for the reference and 6.18 hashes/s for flattening. Static growth did not rank throughput losses consistently. Longer runs and controlled builds remain in progress.')
s = s.replace('結果は今回の入力・標本・条件に限られ，複数実装の長時間評価と静的変化の関係の検証は継続中である．', 'xmr-wasmの5標本でも公表された期待値との一致と30秒以上の3反復を確認した．平坦化の機構を持つ版は命令数1.166倍，速度比0.678で，命令増加の順位と速度低下の順位は一致しなかった．結果は今回の入力・標本・条件に限られ，長時間評価とビルド条件をそろえた対照は継続中である．')
p.write_text(s, encoding='utf-8')
draft = '''CSEC 2026年12月研究会：発表申込案（未送信）
和文タイトル：公開WebAssembly採掘データセットにおける難読化とハッシュ計算性能の実証分析
英文タイトル：An Empirical Analysis of Obfuscation and Hashing Performance in Public WebAssembly Mining Datasets

和文概要案：
公開WebAssembly採掘データセットを対象に，難読化の機構と，正しいハッシュ計算を実行した際の性能を分析する．配布設定と命令列の機構を照合し，通常の処理や研究用計測の特徴と区別する．既存の静的解析に加えて，Proof-of-Theftの2つの配布実装について公表テストベクトルによる出力照合と反復速度測定を行った．xmr-wasmの平坦化版では，分岐表を用いない状態による処理選択を確認し，基準版との速度と命令数の違いを実測した．静的な増加量と速度低下の順位は一致せず，配布物の名称と設定の不一致や最適化条件による交絡も確認した．これらを区別して，検出評価を中心とする公開標本に対し，ハッシュ出力・速度・難読化機構の対応を追加する．今後はビルド条件をそろえた対照と他の公開標本への比較拡張を行う．

English abstract draft:
We analyze obfuscation mechanisms and validated hashing performance in public WebAssembly mining datasets. We distinguish declared transformations from observed mechanisms, normal processing, and research instrumentation. Beyond prior static analysis, we check public hash vectors and repeatedly measure two distributed implementations in the Proof-of-Theft artifact. The flattened xmr-wasm wrapper exhibits state-based dispatch without a branch table. Static growth does not consistently rank throughput loss. Directory/build discrepancies and optimization differences limit causal interpretations. This study adds a traceable correspondence between hash outputs, throughput, and mechanism evidence to artifacts mainly evaluated for detection. Controlled builds and additional public samples remain planned extensions.

確認済みの成果：10標本で適用可能な公表CN/0ベクトルに一致．xmr-wasmの5標本は30秒以上・3反復完了．webminerpoolhashcnの5標本は5秒・3反復の予備測定．Cryptic Bytesの2標本は既存の約1000秒のプール実験を再利用．全件評価，完全網羅，世界初，採択は主張しない．
先行研究との差：Proof-of-Theftの本文・補足に同標本の出力と反復hashes/sの比較報告は確認できていない．hashrate.jsの存在により，過去に測定そのものがなかったとは断定しない．他研究には既存の性能評価がある．
公式募集：https://www.ipsj.or.jp/kenkyukai/event/eip114spt65csec115.html
申込締切：2026-10-09 23:59 JST．原稿締切：2026-11-12 23:59 JST（公式の曜日表記に不整合があり通知で照合要）．申込・投稿はユーザー自身の操作．
'''
(ROOT / 'experiments/runtime-reference/csec-submission-draft.txt').write_text(draft, encoding='utf-8')
print('Integrated completed xmr measurements and refreshed concrete submission draft')
