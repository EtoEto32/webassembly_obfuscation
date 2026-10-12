"""Reorganize reviewed mechanisms for the paper; retain detailed evidence separately."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex'
old=p.read_text(encoding='utf-8')
start=old.index('\\subsection{実行評価対象での機構と配布設定の照合}')
end=old.index('\\subsection{RQ1への回答}',start)
block=old[start:end]
lines=block.splitlines()
def paragraph(prefix):
    found=[x for x in lines if x.startswith(prefix)]
    assert len(found)==1,prefix
    return found[0]
substitution=paragraph('命令置換版の公開hash関数にも')
split=paragraph('分割設定版では')
controls=paragraph('この比較は，通常の数値処理')
linked=paragraph('\\paragraph{RQ2の標本との対応}')
toolchain=paragraph('emcc-obfの公開説明では')
replacement='''\\subsection{実行評価対象での機構と配布設定の照合}
\\label{sec:proof-mechanisms}
RQ2の実測対象について，配布設定と実際の命令列を照合した．Proof-of-Theftのwebminerpoolhashcnでは，配布基準と4変換ディレクトリのMakefileがすべて\\texttt{-enable-bcfobf}を指定していた．設定と名称が一致せず，過去の生成指示も確定できないため，後節の速度は配布標本間の比較とし，4手法のオーバーヘッドには用いない．xmr-wasmでは名称に対応するフラグがあり，5標本に同梱されたC/C++・ヘッダ46ファイルは相対パスとSHA-256で基準版と一致した．配布ソース上の対応は確認できるが，過去のコンパイラ，入力，オブジェクトファイルまで同一だったとは保証しない．

\\paragraph{平坦化の機構と適用箇所}xmr-wasmの公開hash関数では，通常版のnonce・target処理に対し，状態を読み出して次の処理を選び，状態を更新して共通ループへ戻る制御を確認した．この関数には\\texttt{br\\_table}がなく，分岐表の存在を必要条件としない具体例である．8・16バイトのXOR補助関数112・118でも，条件検査，XORと書込み，添字更新，終了を状態で表すように変わった．通常版との引数，上限8・16，増分1の対応を確認した．コンテキスト初期化83，鍵取り込み82，解放86にも同じ機構があり，それぞれ4・24・8状態をレビューした．引数検査や確保・コピー・解放と，同梱OpenAESソースの処理が対応するが，全入力の同値性や過去のビルドとの同一性の証明ではない．

\\paragraph{呼出し位置と今回の測定経路}通常版の関数111では，補助関数118の2呼出しが主ループ内にある．一方，初期化・鍵取り込み・解放の呼出しは構造化ループ外にあり，ハッシュごとの処理と主ループ内の処理を区別する．関数112の最初の呼出しはvariant 1の条件内である．関数113でも平坦化の入口と最初の条件を確認し，初期化命令列239行を通常版と対応付けたが，全状態の意味は未確認である．同梱CryptoNightR用演算生成処理と特徴が対応し，呼出しにはvariantが4以上という条件がある．通常版と平坦化版の呼出しまでの命令列は局所変数名を対応付けると一致する．今回の3入力は先頭バイトが7未満でvariant 0を選ぶため，この呼出し経路には入らない．機構の存在と実測中の経路を分け，動的な回数や時間寄与を存在だけから決めない．各状態値，命令位置，対応するソース抜粋は保存した解析記録に残した．

'''+substitution+'\n\n'+split+'\n\n'+toolchain+'\n\n'+controls+'\n\n'+linked+'\n\n'
backup=ROOT/'paper/revisions/before-rq1-mechanism-compact-20261008/main.tex'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():backup.write_text(old,encoding='utf-8')
new=old[:start]+replacement+old[end:]
p.write_text(new,encoding='utf-8')
report=dict(original_subsection_characters=len(block),revised_subsection_characters=len(replacement),
    unchanged_measurements=True,backup=str(backup),
    preserved=['Source/build uncertainty','State dispatcher mechanism','XOR loop correspondence','OpenAES states',
               'Variant4 guard excluded for v0','Arithmetic derivation','Unconfirmed split mechanism',
               'Instrumentation controls','13-artifact evidence correspondence'],
    limitation='Editorial source compression only; final PDF and page count not verified.')
(ROOT/'results/runtime-mining/cross-dataset/rq1-presentation-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'RQ1 subsection {len(block)} -> {len(replacement)} characters; detailed evidence preserved.')
