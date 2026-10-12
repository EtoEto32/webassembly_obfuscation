"""Connect the mining-specific ordinary-code control to RQ1 and RQ2."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'paper/main.tex'
t=p.read_text(encoding='utf-8')
anchor='この比較は，通常の数値処理に分岐表が現れる例と，平坦化でも分岐表が現れない例を合わせて，静的な指標の有無だけでは判断できないことを示す．'
addition='通常処理の対照として，xmr-wasmの配布基準にも命令列を解釈する構造がある．関数111では，opcode，宛先・参照元の番号を読み出す処理と70箇所の分岐表が，同梱CryptoNightRの\\texttt{v4\\_random\\_math}による演算選択の展開と対応した．最初の選択と乗算処理を通常版・平坦化版で確認すると，分岐表が比較と条件分岐へ変わっていた．しかし状態を更新するdispatcherの追加とは区別する．暗号アルゴリズム自身が命令列を解釈する場合もあり，この構造の存在だけを難読化の仮想化の根拠にはしない．全70箇所の各処理の同値性は未確認である．\n\n'
assert t.count(anchor)==1
if addition not in t:t=t.replace(anchor,addition+anchor)
anchor2='未実行コードがコンパイルや配置へ与える間接的影響は別途未検証である．'
addition2='通常版にある70箇所の分岐表もvariant 4以上の同じ条件内にあり，今回のv0ではその経路を通らない．従って分岐表の消失だけから，v0の速度低下を説明しない．'
assert t.count(anchor2)==1
if addition2 not in t:t=t.replace(anchor2,anchor2+addition2)
p.write_text(t,encoding='utf-8')
print('RQ1 mining-native interpreter control and RQ2 measured-path caveat added.')
