"""Connect reviewed replacement expressions to actual evaluated paths."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = ROOT/'paper/main.tex'
s = p.read_text(encoding='utf-8')
marker = 'この比較は，通常の数値処理に分岐表が現れる例と，'
if '1368051000' not in s:
    s = s.replace(marker, r'''命令置換版の公開hash関数にも，元の式との対応を確認した．入力先頭のバイト$x$からvariantを求める式$x-6$は，定数$C=1368051000$を用いた$(x-C)-6+C$に置き換わる．nonceの更新$n+1$は$n-(0-1)$に置き換わる．どちらもWasmの32ビット整数の剰余演算で元の式と一致し，単に演算命令の多さから置換と推定した例ではない．ただし今回のv0入力では先頭バイトが7未満なので前者の経路を通らず，最大targetでnonceの変化がないため後者の経路も通らない．この機構確認と，後節の測定中に実行された処理を区別する．ハッシュ本体の他の式の確認は継続中である．

''' + marker, 1)
s = s.replace('ただし置換版の具体的な式と適用関数の確認は未完了であり，増加した全命令が実行されたとは扱わない．', '置換版のhashラッパでは2つの同値式を確認したが，両式とも今回の測定では通らない経路にある．ハッシュ本体の適用範囲は未確認であり，増加した全命令が実行されたとは扱わない．')
p.write_text(s, encoding='utf-8')
print('Integrated substitution identities and excluded-path caveat')
