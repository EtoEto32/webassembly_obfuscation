# -*- coding: utf-8 -*-
"""Prepend a dated result to the relevant research files, preserving history."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MARKER='共同多項式更新候補（2026-10-18）'
notes={
 'research/STATUS.md':'''[共同多項式更新候補](polynomial-carrier/README.md)を実Wasm変換器と2経路の回復器へ実装した。36主条件と36回復バイナリ、Node 75,024呼出し・WABT 288呼出しで不一致0。一括再現で72本のbyte一致を確認。解析費用は未変換比約3.0–4.5倍だが、明示復号方式とほぼ同じであり、ASPIREの多項式構成等が近い。復元成功自体を失敗理由にせず、増分効果と技術差が弱いため主方式には不採用。新規で有効な主発明と特許性の確立は未達。goalはactive。''',
 'research/literature-review.md':'''[多項式構成と公報の照合](polynomial-carrier/prior-art.md)を追加。ASPIRE D2.01（2014公開技術報告）の§11.1.2–11.1.4とUS7966499B2の本文・請求項1–22を確認した。可逆変換の前後合成、多項式展開、単項式共有、有限環上の同値式置換を既知要素として認める。全公報調査・審査経過の確認とは区別する。''',
 'research/research-gap.md':'''[公開出力から更新則へ戻る2経路](polynomial-carrier/analysis.md)を追加。状態を混ぜて展開しても、線形逆像または既知の乗算因子を順にたどれる構造では、独立した追加負担を得られなかった。式の密度や個別復号構文の消失と、意味回復費用を分ける。''',
 'research/candidates.md':'''[非線形更新の共同多項式化](polynomial-carrier/plan.md)を実装・評価した。有限状態列挙とは別原理だが、既知の座標変換・多項式構成との近さが判明した。SIMD融合は一部高速化したものの、decodeに対する回復費用の増分が支持されず主方式に不採用。選ばなかった2方向を新発明として件数へ加算しない。''',
 'research/threat-model.md':'''[共同多項式候補の課題](polynomial-carrier/analysis.md)は、全バイナリと方式から簡潔な同値更新を回復すること。元行列・元ソース・seedを解析器に渡さない。公開出力を足掛かりに線形逆像と既知因子の2経路を試した。選択解析の反復時間、抽出時間、解析器開発時間の未測定を区別し、人の難しさへ読み替えない。''',
 'research/algorithm.md':'''[共同多項式候補の疑似コード](polynomial-carrier/plan.md)と[実Wasm CLI](polynomial-carrier/prototype.py)を追加した。4状態の更新を有限環上で共役変換し、単項式の4出力係数をi32x4にまとめる。限定テンプレートとWasm validationで入力を制約する。主方式に採用したものではない。''',
 'research/novelty-analysis.md':'''[共同多項式候補の構成対応表](polynomial-carrier/prior-art.md)を追加。ASPIREの前後合成、多項式実装、公報の有限環同値式が近い。Wasmでの厳密な整数意味とSIMD配置の差はあるが、それだけで特許の核とはしない。実行時間の短縮と新規性・解析負担の増分を別々に判定した。''',
 'research/experiments.md':'''[共同多項式候補の実測](polynomial-carrier/analysis.md)を追加。3カーネル×4方式×raw/O2/O3、108 fresh process、36更新則回復、主72本75,024呼出し、WABT 288呼出し、3,072任意状態、追加72基底条件を保存。coupled O3未変換側の旧抽出未対応1件を修正し、最終条件の未対応・crash・timeout・誤答を各0とした。''',
 'research/patent/README.md':'''[共同多項式候補の先行構成対応](../polynomial-carrier/prior-art.md)を追加。ASPIREの可逆写像を前後に置く多項式構成と、US7966499B2請求項1–22の有限環上の同値式置換を確認。固定128bit SIMDでの共同計算だけでは主発明として弱く、明示復号比の追加解析負担も未支持のため不採用。権利範囲・有効性・実施自由の法的判断は行っていない。''',
 'paper-draft.md':'''[共同多項式更新候補の日本語論文ノート](research/polynomial-carrier/paper-note.md)と[実装・再現手順](research/polynomial-carrier/README.md)を追加した。主72本75,024呼出しの一致、36/36更新回復、未変換比の解析費用増加とdecode比の増分未支持を記録。新発明の完成や既存草稿の成功件数には合算しない。'''
}
for name,note in notes.items():
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if MARKER in text:continue
    first,rest=text.split('\n',1)
    path.write_text(first+'\n\n'+MARKER+'：'+note+'\n'+rest,encoding='utf-8')
print('Updated research ledger; root README and paper sources preserved.')
