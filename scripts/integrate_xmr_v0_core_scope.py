"""Reflect core-scope comparison in the current manuscript, preserving numbers."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex';text=p.read_text(encoding='utf-8')
anchor='各状態値，命令位置，対応するソース抜粋は保存した解析記録に残した．'
addition='さらに関数111では，平坦化版の本体命令列の増加はvariant 4以上のブロック内に収まった．そのブロックを除く3,609行は，局所変数とラベルの名前を対応付けると命令，数値オペランド，参照する局所変数の型が一致した．これは本体内の比較であり，呼出し先の変化やモジュール全体の同値性を否定・証明するものではない．'
assert text.count(anchor)==1
if addition not in text:text=text.replace(anchor,anchor+addition)
anchor2='従って分岐表の消失だけから，v0の速度低下を説明しない．'
addition2='関数111の本体命令列は，この未実行ブロック内で9,428行増え，それ以外は名前を対応付けると一致した．したがって，本体の増加分をそのままv0で追加実行された処理とは扱えない．補助関数の変換に加え，増えた局所変数の宣言やコンパイル・配置の違いを分ける追加評価が必要である．ここでの行数は保存WATの命令列の差であり，動的命令数やファイルのバイト増加量ではない．'
assert text.count(anchor2)==1
if addition2 not in text:text=text.replace(anchor2,anchor2+addition2)
p.write_text(text,encoding='utf-8')
print('RQ1 retained core correspondence and RQ2 excluded-growth interpretation reflected.')
