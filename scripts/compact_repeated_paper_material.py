"""Reduce duplicate presentation in the existing paper while retaining evidence."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex';before=p.read_text(encoding='utf-8');s=before
backup=ROOT/'paper/revisions/before-runtime-presentation-compact-20261008'
backup.mkdir(parents=True,exist_ok=True)
if not (backup/'main.tex').exists():(backup/'main.tex').write_text(before,encoding='utf-8')
removed=[]
for label in ('fig:proof-throughput','fig:xmr-runtime'):
    pattern=r'\\begin\{figure\*\}.*?\\end\{figure\*\}'
    blocks=list(re.finditer(pattern,s,re.S))
    match=next((m for m in blocks if '\\label{'+label+'}' in m[0]),None)
    if match:
        removed.append(label);s=s[:match.start()]+s[match.end():]
s=s.replace('表\\ref{tab:xmr-runtime}と図\\ref{fig:xmr-runtime}はこの完了した測定を示す．',
            '表\\ref{tab:xmr-runtime}に実測速度と命令数比を示す．',1)
start=s.find('さらに関数111から呼ぶ補助関数112では，')
end=s.find('\n\n命令置換版の公開hash関数にも，',start)
assert start>=0 and end>start
compact=r'''関数111から呼ぶ8バイトXOR補助関数112でも，通常版のループが状態による選択へ変わる．変換版は状態をオフセット16，そのポインタを12，添字を20に保持し，条件確認，XORとバイト書込み，添字更新，条件確認への戻り，終了を別の状態で表す．通常版と2ポインタ引数，上限8，増分1が対応する．16バイトXOR補助関数118にも同様の機構があり，その2呼出しは通常版の主ループに直接含まれる．いずれも\texttt{br\_table}はない．一方，関数112の最初の呼出しはvariantが1の条件内にあるため，v0測定への寄与を存在だけから説明しない．各状態値と命令位置は保存した解析記録に残す．呼出しの構造上の位置と，動的な経路・回数を区別する．'''
s=s[:start]+compact+s[end:]
# Correct a leftover optimization caveat placed in the unrelated implementation's results.
old='xmr-wasmの偽制御フロー版には他の版と異なり明示的な\\texttt{-O2}があるため，これも通常版との手法効果の比較から分離する．'
assert old in s;s=s.replace(old,'',1)
labels=re.findall(r'\\label\{([^}]+)\}',s)
refs=re.findall(r'\\(?:ref|pageref)\{([^}]+)\}',s)
assert not set(refs)-set(labels)
assert len(labels)==len(set(labels))
assert s.count('\\begin{document}')==s.count('\\end{document}')==1
p.write_text(s,encoding='utf-8')
report=dict(before_characters=len(before),after_characters=len(s),
            removed_duplicate_main_figures=removed,
            preserved='All raw measurements, numeric tables, static/throughput ratios, original figure files, mechanism JSON/WAT and finite-output limitations.',
            source_reference_check='No unresolved or duplicate labels.',
            pdf_page_count='Unverified: built-in compiler environment failure.',
            backup=str(backup/'main.tex'))
out=ROOT/'results/runtime-mining/cross-dataset/paper-presentation-compaction.json'
out.write_text(json.dumps(report,indent=2)+'\n')
with (ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/resume-state.txt').open('a',encoding='utf-8') as f:
    f.write('\n原稿の重複整理：compact_repeated_paper_material.pyでwebminerpool/xmrの表と重なる2図を本文から除き，図ファイル自体と数値表・比・生ログは保存。helper平坦化の状態定数列を解析記録へ委ね，機構/ポインタ/添字/条件/戻り/variant範囲を保持して説明を圧縮。別実装wmp節に紛れたxmr-O2説明はxmr専用節に残して重複除去。label参照と重複ラベル検査は通過。バックアップと差分要約保存。6--8pageは未検証，新規実測なし。利用枠21%使用/79%残。\n')
print(json.dumps(report,indent=2))
