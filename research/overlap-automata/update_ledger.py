# -*- coding: utf-8 -*-
"""Add this bounded negative result to the research ledger, preserving history."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MARKER='状態重なりNFA候補（2026-10-18）'
notes={
 'research/STATUS.md':'''[状態重なりNFA候補](overlap-automata/README.md)を実Wasm変換器とバイナリのみを入力とする回復器へ実装した。主72本・148,680呼出し、WABT288呼出し、i64境界6本・12,390呼出しで不一致0。全36主条件・4解析経路で等価DFAを回復し、108 fresh processで費用を測定。70追加モデルでも全280解析が回復した。重なり優先の規則は安全な無作為結合より一貫した費用増加を示さず主方式には不採用。右言語が互いに素な元状態では重なり自体を作れない必要条件を説明し、既知NFA構成・公開特許と照合した。一括再現で72本の一致を確認。実装・測定・反証の進捗であり、新規で有効な主発明と特許性の確立は未達。goalはactive。''',
 'research/literature-review.md':'''[追加の文献・公報照合](overlap-automata/prior-art.md)を保存した。Brzozowski/Tammの2013年プレプリント§4–5、Clemente/MayrのLMCS2019誌面§7.2等、US11657127B2の請求項1–17とFSM重畳の記載を確認。Kameda–Weiner原論文の直接精読、上記公報の請求項18末尾・全図面の精読は未完了として区別する。状態共有・合法な商の構成だけを新規性としない。''',
 'research/research-gap.md':'''[状態重なりの成立条件と反証](overlap-automata/analysis.md)を追加。異なる元状態の右言語が互いに素なら、同値なtrim NFAで複数の元状態に対応する有効状態を作れない。重なりが可能な例でも、元の対応を回復せず等価DFAを再構成できる。次の候補は、表現の曖昧さと実用的な意味回復費用を別々に検査する。''',
 'research/candidates.md':'''[元DFAで検証しながらNFA状態を重ねる案](overlap-automata/plan.md)を追加の反証候補として実装・比較した。共有relayとは異なる原理だが、既知のNFA構成と状態共有からの差は主に選択目的にあり、その追加効果が弱かった。新発明を一件確立したとは数えない。[実測と採否](overlap-automata/README.md)。''',
 'research/threat-model.md':'''[状態重なり候補の解析課題](overlap-automata/analysis.md)では、元状態番号やseedではなく同じ言語を受理する簡潔なDFAを回復対象にした。方式・全バイナリ既知で4経路を比較。抽出器は元DFA・生成JSONを読まず、正当性の採点のみ元DFAを使う。独自解析器の開発費用、人間の解析時間、公開I/O学習は未測定。''',
 'research/algorithm.md':'''[状態重なり候補の設計と意味保存](overlap-automata/analysis.md)、[疑似コード](overlap-automata/plan.md)、[実バイナリCLI](overlap-automata/prototype.py)を追加。全語を受理する補助NFAとの積、安全な状態結合、重なり優先選択、i64集合更新を実装した。主方式には不採用であり、以下の旧条件付き選定を新しい成功案へ読み替えない。''',
 'research/novelty-analysis.md':'''[状態重なり候補の構成対応表](overlap-automata/prior-art.md)を追加した。積、NFA状態共有、言語保存検査、bitset実行は既知。重なり優先の探索規則を差として実験したが、同費用の無作為結合より一貫した保護効果を確認できなかった。独立した新規性・特許性を確定せず、主方式には不採用。''',
 'research/experiments.md':'''[状態重なり候補の実測・再現](overlap-automata/README.md)を追加。3カーネル×4方式×raw/O2/O3、回復36本、4解析経路、3 fresh process/条件を比較した。70モデル条件と120例のsimulation簡約検査、unsafe mergeとbit63の対照も別記録。旧screenのdead-state得点、旧解析器の未対応4件、同時実行された旧性能ログを主結果から区別する。''',
 'research/patent/README.md':'''[状態重なり候補の構成・先行技術対応](../overlap-automata/prior-art.md)を追加。US11657127B2の請求項1–17とFSM重畳の記載を比較した。鍵付きnetlist lockingと今回の言語保存NFA化の相違はあるが、補助機械の積や状態共有一般を発明とはしない。重なり優先規則の保護効果が弱く、出願の核となる主方式には採用しない。''',
 'paper-draft.md':'''[状態の対応を重ねるNFA変換の日本語草稿](research/overlap-automata/paper-note.md)と[実装・測定・再現](research/overlap-automata/README.md)を追加した。主72本・148,680呼出しとWABT288呼出しの一致、36/36回復、70モデル条件の反証を保存。追加した選択規則の効果が弱い負の結果であり、本文の件数や新規性に合算せず、新発明の完成とはしない。'''
}
for name,note in notes.items():
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if MARKER in text:continue
    first,rest=text.split('\n',1)
    path.write_text(first+'\n\n'+MARKER+'：'+note+'\n'+rest,encoding='utf-8')
print('Updated research ledger; unrelated README and paper sources preserved.')
