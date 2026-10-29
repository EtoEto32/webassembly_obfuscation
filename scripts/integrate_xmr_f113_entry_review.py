"""Insert only the reviewed f113 scope; preserve all other paper content."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'paper/main.tex'
t=p.read_text(encoding='utf-8')
anchor='関数111内の2呼出し位置はいずれも構造化ループ外であり，主ループ内の処理とは区別する．'
addition='関数113でも状態をオフセット16に保持し，共通ループへ戻る機構を確認した．入口状態$295792562$の初期化処理239行は，局所変数の対応と一時領域の座標差を除いて通常版と一致し，状態$-1569009996$へ進む．そこで一時領域の値と45を比較して次の状態を選ぶ．ただし確認範囲は入口と最初の条件に限り，全状態の意味と元ソースの関数名は未確認である．'
assert t.count(anchor)==1
if addition not in t:t=t.replace(anchor,anchor+addition)
p.write_text(t,encoding='utf-8')
print('RQ1 f113 entry evidence added with explicit partial-review limitation.')
