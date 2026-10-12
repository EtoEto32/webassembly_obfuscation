"""Reflect measured-path guard in RQ1/RQ2 without changing runtime results."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'paper/main.tex'
t=p.read_text(encoding='utf-8')
anchor='ただし確認範囲は入口と最初の条件に限り，全状態の意味と元ソースの関数名は未確認である．'
addition='同梱ソースのCryptoNightR用演算生成処理と，height引数，種のバイト値，初期化の構造が対応する．呼出し側ではvariantが4以上の場合に限ってこの処理へ進む．通常版と平坦化版の呼出しまでの命令列は，局所変数名を対応付けると一致した．今回の3入力は先頭バイトが7未満でvariant 0を選ぶため，この呼出し経路には入らない．'
assert t.count(anchor)==1
if addition not in t:t=t.replace(anchor,anchor+addition)
anchor2='その他の処理も測定時間に含まれるため，これらの機構だけから低下の全量を説明しない．'
addition2='関数113では平坦化の入口を確認したが，variant 4以上に限定された呼出しは今回のv0入力では通らず，その直接の実行負荷を速度低下の根拠にはしない．未実行コードがコンパイルや配置へ与える間接的影響は別途未検証である．'
assert t.count(anchor2)==1
if addition2 not in t:t=t.replace(anchor2,anchor2+addition2)
p.write_text(t,encoding='utf-8')
print('RQ1 source/path correspondence and RQ2 excluded direct-overhead interpretation added.')
