"""Correct declared-label interpretation and connect refreshed RQ1/RQ2 evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'paper/main.tex'
s = p.read_text(encoding='utf-8')
s = s.replace('公開WebAssemblyデータセットに含まれるクリプトジャッキング関連プログラムでは，どのような難読化手法が確認され，データセットごとにどのような傾向があるか．', '公開WebAssembly採掘データセットにはどのような難読化手法と実装上の仕組みが確認され，通常処理・研究用計測コードとどのように区別できるか．データセット・実装ごとにどのような傾向があるか．')
s = s.replace('Proof-of-Theftの通常版と4種類の変換版は，記録済みの受理ハッシュ13件すべてと一致した．', 'Proof-of-Theftのwebminerpoolhashcnの配布基準と4つの変換名ディレクトリの標本は，記録済みの受理ハッシュ13件すべてと一致した．ただし同梱のビルド設定とディレクトリ名には不一致があり，手法別の効果とは解釈しない．別実装のxmr-wasmでは5標本が公表されたCryptoNightの期待値と一致し，平坦化版の状態による処理選択を確認した．')
s = s.replace('An original and four obfuscated Proof-of-Theft artifacts matched all 13 recorded accepted hash outputs and underwent short repeated throughput measurements.', 'Five Proof-of-Theft webminerpoolhashcn artifacts matched all 13 recorded accepted hash outputs and underwent short repeated measurements. Their directory labels conflict with distributed build settings, so their rates are not attributed to distinct obfuscation methods. Five xmr-wasm artifacts matched applicable public CryptoNight vectors, and we verified state-based dispatch in the flattened hash wrapper.')
marker = '\\subsection{RQ1への回答}'
if '\\label{sec:proof-mechanisms}' not in s:
    pos = s.index(marker)
    s = s[:pos] + r'''\subsection{実行評価対象での機構と配布設定の照合}
\label{sec:proof-mechanisms}
RQ2の追加対象も，ディレクトリ名，ビルド指示，バイナリの機構を照合する．Proof-of-Theftのwebminerpoolhashcnでは，配布基準と，flattening，split，substitution，boguscfという4ディレクトリのMakefileがいずれも\texttt{-enable-bcfobf}を指定する．これはファイルの名前と同梱設定の不一致であり，配布基準が非難読化であることも，4種類の変換が実際に適用されたことも，この資料だけでは確定できない．ビルド時に別の指示を使った可能性があるため，バイナリがすべて同じ手法で加工されたとも断定しない．したがって，後節の速度は配布標本間の比較として残し，4手法のオーバーヘッドには用いない．

xmr-wasmでは平坦化，命令置換，分割，偽制御フローのディレクトリ名に対応するフラグを確認した．さらに平坦化版の公開hash関数を通常版と比べると，スタック領域のオフセット8に状態値を格納し，その値を読み出して複数の定数と比較し，処理を選択する．別のオフセット4に状態の格納先へのポインタを保持し，各処理からこのポインタ経由で次の状態を更新して共通ループへ戻る．例えば初期状態は$-518616621$で，処理後に$573433544$へ更新する経路がある．通常版のnonceとtargetを扱うループとは制御の表現が異なる．このhash関数に\texttt{br\_table}はなく，分岐表を使わない平坦化の具体例である．関数全体の状態遷移と元ソースの処理との完全な対応を証明したわけではないが，単なる分岐命令の存在より強い機構の根拠を得た．

この比較は，通常の数値処理に分岐表が現れる例と，平坦化でも分岐表が現れない例を合わせて，静的な指標の有無だけでは判断できないことを示す．またWasabiのhook importを持つ版を除外し，非計測版の機構を確認することで，計測の追加処理を難読化の根拠に混ぜない．旧予備実験のA-StarとCreaturePackの命令列復元は，計測コードとの区別を確認する対照として再利用する．

''' + s[pos:]
s = s.replace('Wasabi計測版を除き，通常版とemcc-obfの平坦化，分割，命令置換，偽制御フローの4版を評価した．', 'Wasabi計測版を除き，配布基準と，平坦化，分割，命令置換，偽制御フローというディレクトリ名の4標本を評価した．第\\ref{sec:proof-mechanisms}節の不一致があるため，名前は変換の確定ラベルではない．')
s = s.replace('仮想化版も追加のWASI処理の照合が未完了である．', '仮想化版も，配布元のJavaScriptを用いた対照呼出しで同種のエラーとなった．アダプタだけに固有の不具合ではないことを確認したが，配布物のビルド・リンクの問題を含む原因の確定は未完了である．')
s = s.replace('両者は未評価理由とともに記録する．', '両者は照合失敗の理由とともに記録する．cryptonight-hashの7標本は非計測版に必要なハッシュ関数のexportがなく，そのままでは同じ評価を実行できない．この制約を出力不一致と混同しない．')
pos = s.index('\\subsection{同一条件の短時間反復測定}')
if '公表テストベクトルによる別実装の照合' not in s:
    s = s[:pos] + r'''\subsection{公表テストベクトルによる別実装の照合}
独立した期待値としてXMRig v6.18.0の\texttt{CryptoNight\_test.h}に公表されたCryptoNight v0の入力5件と出力を用いた\cite{xmrigvectors}．webminerpoolhashcnの5標本は配布元のcn.jsから呼び出して5件全件が一致した．xmr-wasmは元ソースで入力先頭の値からvariantを選択するため，公表入力のうちv0に対応する3件を使用し，通常版と4変換版で全件一致した．後者の公開hash関数はtargetを満たすまでnonceを進めるが，最大targetを与え，確認した出力ではnonceが変化せず1回のハッシュに対応することも確かめた．デモのmainは実行せず，ネットワークも無効にした．これは有限のテストによる確認であり，全入力に対する意味保存の証明とは区別する．

''' + s[pos:]
s = s.replace('\\caption{Proof-of-Theftの予備測定（3反復，H/s）}', '\\caption{webminerpoolhashcn配布標本の予備測定（3反復，H/s．変換名はディレクトリ名で，適用手法の確定ではない）}')
s = s.replace('設定 & 中央値 & 最小 & 最大', '配布名 & 中央値 & 最小 & 最大')
s = s.replace('通常版 & 204.04', '配布基準 & 204.04')
s = s.replace('予備測定の速度と，同一配布通常版に対するサイズ・命令数・速度比．', '予備測定の速度と，配布基準に対するサイズ・命令数・速度比．図中のOriginalは配布基準，その他の名称はディレクトリ名である．同梱設定との不一致があり，手法別の効果とは解釈しない．')
s = s.replace('配布標本のビルド・最適化条件の違いと他のホスト処理の負荷を完全には分離していないため，速度比を難読化だけの因果効果とは扱わない．', '配布名と設定の不一致に加え，ビルド・最適化条件と他のホスト処理の負荷を完全には分離していないため，速度比を難読化だけの因果効果とは扱わない．xmr-wasmの偽制御フロー版には他の版と異なり明示的な\\texttt{-O2}があるため，これも通常版との手法効果の比較から分離する．')
p.write_text(s, encoding='utf-8')
bib = ROOT / 'paper/references.bib'
t = bib.read_text(encoding='utf-8')
if '@misc{xmrigvectors,' not in t:
    t += r'''
@misc{xmrigvectors,
  author = {{XMRig developers}},
  title = {{CryptoNight} test vectors, {XMRig} v6.18.0},
  howpublished = {\url{https://github.com/xmrig/xmrig/blob/v6.18.0/src/crypto/cn/CryptoNight_test.h}},
  note = {Accessed 2026-10-08}
}
'''
    bib.write_text(t, encoding='utf-8')
print('Corrected label interpretation and linked refreshed RQ1/RQ2 evidence')
