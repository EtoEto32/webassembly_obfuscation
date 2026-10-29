"""Add reviewed key-import scope to the existing paper, preserving other edits."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex'
t=p.read_text(encoding='utf-8')
anchor='ハッシュ計算ごとに実行される可能性はあるが，動的な回数は未測定であり，機構の存在だけで測定時間への寄与を決めない．'
addition='鍵取り込みの関数82でも，通常版の引数・鍵長検査，確保，コピー，展開，解放，戻り値の処理が24状態へ変わった．状態はオフセット8，そのポインタは4に保持される．通常版と呼出し列が一致し，同梱\\texttt{oaes\\_key\\_import\\_data}の処理との対応も確認したが，全入力の同値性は証明していない．関数111内の2呼出し位置はいずれも構造化ループ外であり，主ループ内の処理とは区別する．'
assert t.count(anchor)==1
if addition not in t:t=t.replace(anchor,anchor+addition)
old='XOR補助関数112・118，初期化の関数83，解放の関数86で確認した'
new='XOR補助関数112・118，鍵取り込みの関数82，初期化の関数83，解放の関数86で確認した'
assert old in t or new in t
t=t.replace(old,new)
p.write_text(t,encoding='utf-8')
print('RQ1 mechanism and RQ2 reviewed scope updated; measured numbers unchanged.')
