"""Reflect verified preliminary results in the existing manuscript."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'paper/main.tex'
s = p.read_text(encoding='utf-8')
s = s.replace('公開WebAssembly採掘プログラムの難読化解析と実行評価に向けた実験設計', '公開WebAssembly採掘データセットにおける難読化とハッシュ計算性能の実証分析')
s = s.replace('Obfuscation Analysis of Public WebAssembly Mining Programs and Experimental Design for Runtime Evaluation', 'An Empirical Analysis of Obfuscation and Hashing Performance in Public WebAssembly Mining Datasets')
s = s.replace('クリプトジャッキングに用いられるWebAssemblyプログラムに難読化を施すと，コード構造・命令数・ファイルサイズはどのように変化するか．', '難読化はハッシュ出力の正しさ，計算速度，コード構造・命令数・ファイルサイズにどのような影響を与えるか．その傾向は複数の採掘実装で共通するか．')
s = s.replace('RQ2では，変換前の基準版と変換後のファイルを対応付けられるデータを用い，手法ごとに変化量を比較する．', 'RQ2では，基準版と変換版を対応付け，静的な変化量に加えて，ハッシュ出力の照合と同一条件の速度測定を行う．')
s = s.replace('ここで測るのは，ファイルを実行せずに調べられるコードの量である．', '静的なコード量と実測したハッシュ計算性能の両方を扱う．')
s = s.replace('採掘機能とハッシュ計算速度の検証方法を別節で示すが，実行評価は未完了である．', '採掘機能と速度の予備実測を別節で示す．複数実装を横断した長時間の反復評価は進行中である．')
s = s.replace('本稿で示す実測結果はコードを実行せずに調べた変化である．加えて，既存研究のRQ3に基づく採掘機能とハッシュ計算速度の検証方法を設計し，実装の準備状況と未確認事項を整理した．採掘性能の実測とプール受理の確認は未完了であり，検出を回避する能力も評価していない．', '加えて，Cryptic Bytesの通常版と偽制御フロー版で外部プールによるshare受理を確認した．Proof-of-Theftの通常版と4種類の変換版は，記録済みの受理ハッシュ13件すべてと一致した．同標本の短時間反復測定を行い，静的な増加量と計算速度を比較した．長時間評価とビルド条件の照合は進行中であり，検出回避能力は評価していない．')
s = s.replace('We also design a runtime evaluation based on the RQ3 methodology of WebAssembly diversification for malware evasion, distinguishing implementation checks from mining measurements. Mining throughput and pool acceptance remain unmeasured.', 'We recorded pool-accepted shares for an original and an obfuscated Cryptic Bytes artifact. An original and four obfuscated Proof-of-Theft artifacts matched all 13 recorded accepted hash outputs and underwent short repeated throughput measurements. Long-duration evaluation and build-condition auditing remain in progress.')
pos = s.index('\\section{対象と分析方法}')
s = s[:pos] + r'''\subsection{既存の性能評価と本研究の追加評価}
Cryptic BytesとWebAssembly diversification for malware evasionはハッシュ速度を評価しており，その対象を初めて性能評価したとは主張しない\cite{harnes2024,cabrera2023}．MineSweeperの表10はWasmとasm.js，CPU利用率による速度差を扱う\cite{konoth2018}．Proof-of-Theftの第6節はグラフの簡約と検出を評価し，確認した本文と補足資料には難読化前後のハッシュ速度と出力の比較結果がない\cite{sermchaiwong2026}．ただし公開コードにhashrate.jsがあるため，過去に測定自体が一切行われていないとは断定しない．SWAMPEDの第IV.D節は実行時間を評価するが，JavaScriptの処理がないためimportを空の関数で置き換える\cite{kim2025}．この測定と，正しいハッシュを最後まで計算した速度を区別する．本研究では，これらの公開標本の出力検証と実測を静的構造変化と結び付ける．別名のデータセットでも同一バイナリや同一ソースの再利用を調べる必要がある．

''' + s[pos:]
a = s.index('\\section{採掘機能と性能の検証設計}')
b = s.index('\\section{考察}', a)
runtime = r'''\section{RQ2：ハッシュ計算の正しさと性能の予備評価}
\label{sec:runtime}
\subsection{環境と正しさの確認}
Windows上のLinuxコンテナで，Wasmを変更せず，公開ソースとJavaScriptに基づくホスト処理を用いた．Cryptic Bytesのcn-pico-trtl通常版とLLVMの偽制御フロー設定bcfobfを2 workerで実行し，本人の機器と公開受取アドレスによる通常採掘としてFastpoolへ接続した．xmrig-proxyは6.18.0である．元論文のCoinHive実装と同じランタイムではなく，1ハッシュごとのworker通信の負荷も含む．1,001サンプルから先頭10件を除き，991件と990差分区間を保存した．通常版で13件，変換版で10件のshareを提出し，すべての受理を記録した．各条件1回の試行であり，性能差の確定には反復が必要である．旧試行の読込み失敗やジョブ更新の不具合は，修正後の完了試行と区別して記録した．

Proof-of-Theftのwebminerpoolhashcnでは，配布されたcn.jsからminifyされたimport/exportと時刻関数の対応を確認した．元のhash\_cnで対応するcn-picoの引数を用いた．Wasabi計測版を除き，通常版とemcc-obfの平坦化，分割，命令置換，偽制御フローの4版を評価した．別の採掘試行で受理された13件のジョブとnonceから入力を復元し，記録された出力を期待値とした．ネットワーク無効のコンテナでNode.jsから計算した結果，5標本すべてで13件全件が一致した．Proof-of-Theft側の標本を新たにプールへ提出した結果ではなく，記録済みの受理出力との照合である．有限の入力の結果であり，全入力の正しさは保証しない．

分割と平坦化を併用したTigress版では，hash\_cnの呼出しで間接呼出しに関する実行時エラーが生じた．ホスト実装，ビルド条件，標本のどこに原因があるかは未確定であり，難読化による機能破壊とは結論しない．仮想化版も追加のWASI処理の照合が未完了である．両者は未評価理由とともに記録する．

\subsection{同一条件の短時間反復測定}
出力を照合できた5標本についてNode.jsの1 workerで同期的に計算し，1秒のウォームアップ後に5秒間を3回測定した．13入力を順に繰り返し，標本順を反復ごとに変えた．速度はハッシュ数を実際の経過時間で割って求め，中央値と最小・最大を示す．イメージID，Node.jsとV8の版，CPU型番，対象と測定コードのSHA-256，生データを保存した．
\begin{table}[t]
\caption{Proof-of-Theftの予備測定（3反復，H/s）}
\label{tab:proof-preliminary}
\centering\small
\begin{tabular}{lrrr}
\hline
設定 & 中央値 & 最小 & 最大 \\
\hline
'''
rows = list(csv.DictReader((ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft/preliminary-summary.csv').open()))
labels = ['通常版', '平坦化', '分割', '命令置換', '偽制御フロー']
for label, row in zip(labels, rows):
    runtime += f"{label} & {float(row['median_hps']):.2f} & {float(row['min_hps']):.2f} & {float(row['max_hps']):.2f} " + '\\\\\n'
runtime += r'''\hline
\end{tabular}
\end{table}
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{../results/runtime-mining/cross-dataset/proof-of-theft/preliminary-throughput.pdf}
\caption{予備測定の速度と，同一配布通常版に対するサイズ・命令数・速度比．速度の線は中央値，エラーバーは3反復の最小・最大であり信頼区間ではない．}
\label{fig:proof-throughput}
\end{figure*}
この測定はブラウザと外部プールを使う長時間実験とは別条件である．配布標本のビルド・最適化条件の違いと他のホスト処理の負荷を完全には分離していないため，速度比を難読化だけの因果効果とは扱わない．元標本同士の比較を予備結果として示し，時間を延ばした反復とビルド条件の対照を今後行う．最終出力の一致も各測定で確認した．

'''
s = s[:a] + runtime + s[b:]
s = s.replace('RQ2では実行せずに確認できるコードの変化に焦点を合わせた．', 'RQ2ではコード変化と正しさを確認したハッシュ計算性能の関係に焦点を合わせた．')
s = s.replace('各ファイルの役割を確定できていないProof-of-Theftは，変換前後の比較に含めていない．', 'Proof-of-Theftの実行比較は役割とホスト処理を照合した部分集合に限られる．')
a = s.index('採掘性能と，変換によって実行時に加わる負荷はまだ評価していない．')
b = s.index('\n\n', a)
s = s[:a] + '実行評価は一部標本に限られる．出力を照合した13件以外の入力と，独立した参照実装や公表テストベクトルによる検証が必要である．プール受理とローカル出力一致，ブラウザ測定とNode.js測定を区別する．長時間の反復，独立した実装への拡張，ビルド条件をそろえた対照は未完了である．命令数だけから性能を推定した数値は示さず，検出回避能力も測定していない．' + s[b:]
s = s.replace('加えて，参照論文のRQ3に沿う採掘機能・性能の検証設計と準備状況を整理した．プール受理と採掘速度の実測は未完了であり，難読化後も採掘機能が維持されたという結論はまだ出せない．', '実行評価では一部の通常版と変換版でshare受理を記録し，Proof-of-Theftの5標本で13件の出力一致と短時間の反復速度測定を行った．結果は今回の入力・標本・条件に限られ，複数実装の長時間評価と静的変化の関係の検証は継続中である．')
p.write_text(s, encoding='utf-8')
print('Updated existing manuscript with saved, completed preliminary measurements')
