# -*- coding: utf-8 -*-
"""Record this candidate without replacing prior findings or unrelated files."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];MARKER='書込み失敗境界の被覆候補（2026-10-18）'
notes={
 'research/STATUS.md':'''[書込み失敗境界の被覆](write-frontier/README.md)を実Wasm変換器へ実装。共通baseのstore列を最大右端で区切り、trap後のmemoryも保存して再配置する。72主条件＋72静的回復、164,196呼出しで不一致0。WABT writer288回・memory読取り16,128回も一致。一括再現で144本一致。静的費用は一部増えたが、公開I/Oだけでも1本2–5回・計234問い合わせで72 cloneを生成し、82,098回の比較に一致。既知store merging・正確な例外との差と保護目標の弱さから主案には不採用。新規で有効な主発明・特許性の確立は未達、goalはactive。''',
 'research/literature-review.md':'''[書込み被覆の先行技術照合](write-frontier/prior-art.md)を追加。GCCの2016年store mergingパッチ本文、Su/Lipasti VEE2007の該当節、US20190163475A1の本文と請求項1–20、Wasm store規則を確認。byte像の合成、正確な例外を守る融合・再実行を既知要素として認める。各資料の精読範囲・未確認範囲を区別した。''',
 'research/research-gap.md':'''[書込みの失敗境界と公開I/O回復](write-frontier/analysis.md)を追加。最大右端は再配置の正当性を与える一方、解析側にも小さな区間分割を与える。引数byteのコピー関係は公開memoryへ直接現れ、ラベル入力と境界probeで各累積像を回復できた。内部命令の配置だけでこの情報を保護する方向は避ける。''',
 'research/candidates.md':'''[書込み失敗境界を保存する被覆案](write-frontier/plan.md)を別原理の候補として実装した。通常の広幅被覆、byte分割、同store数の乱択と比較。境界優先の代理目的に一部の処理費用増加はあるが、公開I/O回復の問い合わせ数を増やせなかった。3つの新発明として件数を増やさず、主案には不採用。''',
 'research/threat-model.md':'''[書込み候補の解析モデル](write-frontier/analysis.md)は、元順序の完全再現ではなく同値なmemory更新を求める。静的bit/byte解析に加え、公開exportだけを使う学習も試した。後者は引数byteコピー族という事前知識に依存する。任意Wasmが数回で学習可能とは主張しない。''',
 'research/algorithm.md':'''[書込み被覆の疑似コード・意味保存](write-frontier/analysis.md)と[実Wasm CLI](write-frontier/prototype.py)を追加。右端の新しい最大値で区切り、最終byte像を、同じ最大右端を最初に触る被覆へ変える。正しいtrap後memoryを確認したが、主難読化方式として採用したものではない。''',
 'research/novelty-analysis.md':'''[書込み被覆の構成対応](write-frontier/prior-art.md)を追加。GCCのbyte像合成と正確な例外の先行技術が近い。区間化と境界横断の選択規則は具体化したものの、既知構成からの独立した保護効果を確立できず、特許の核には採用しない。''',
 'research/experiments.md':'''[書込み被覆の測定](write-frontier/analysis.md)を追加。72主条件、静的回復72本、216 fresh process、bit/byte解析、同store数の乱択対照を比較。400モデル132,000比較、誤変換2件、拒否3件、最小被覆の独立BFSも保存。公開I/O回復72本の82,098比較は主実験と入力が重複するため独立標本数には合算しない。''',
 'research/patent/README.md':'''[書込み被覆の先行構成対応](../write-frontier/prior-art.md)を追加。US20190163475A1請求項1–20のstore fusionと例外時の非融合再実行、GCCのstore mergingを確認。今回は静的な右端条件を使うソフトウェア変換でありhardware方式と同一請求項と断定しない。ただし融合時の例外保存という課題自体は既知で、保護上の増分も弱いため主案には不採用。''',
 'paper-draft.md':'''[書込み失敗境界の被覆に関する日本語草稿](research/write-frontier/paper-note.md)と[実装・再現](research/write-frontier/README.md)を追加。144本164,196呼出しの一致、静的72/72回復、公開I/Oの234問い合わせによる72 clone回復を報告。限定的な費用増加と保護目標の弱さを分離し、新発明の完成や既存本文の成功件数へ合算しない。'''
}
for name,note in notes.items():
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if MARKER in text:continue
    first,rest=text.split('\n',1);path.write_text(first+'\n\n'+MARKER+'：'+note+'\n'+rest,encoding='utf-8')
print('Updated research ledger; root README and paper sources preserved.')
