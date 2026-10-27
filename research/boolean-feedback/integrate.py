# -*- coding: utf-8 -*-
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
entries={
'research/candidates.md':('2026-10-23追補：非共役なBoolean残差補正','[設計と3段階の検査](boolean-feedback/README.md)。可逆座標変換に依存しない補正器を全数合成し、bitwise、整数持上げ、任意切替族による群結合を実装した。同じ案の改良を別原理の3案とは数えない。bitwise全12、word全6、切替全6条件をそれぞれ適応解析で回復。小さい群の意味上の抽出が残り、主特許候補には不採用。'),
'research/algorithm.md':('2026-10-23補足：Boolean残差と切替族','[残差更新の定義](boolean-feedback/plan.md)、[整数への持上げの論証](boolean-feedback/word-lifting-plan.md)、[任意切替の生成則](boolean-feedback/coupled-results.md)。N(0)=0、全三角Fに対する有限収束を選定条件とし、H=F XOR N(s XOR F)を配布する。切替版は遷移和集合のrankを検査してから後続stateへselectorを接続する。新規性・特許性・実用的保護効果は未確立。'),
'research/threat-model.md':('2026-10-23追補：Boolean補正器の公開binary解析','解析者は方式と評価器を知り、raw/O3のbinaryを読める。F・Nの選択metadata・群境界・seedは渡さない。目標は元source文字列の一致ではなく、同じ全入力意味を持つ簡潔な非反復Wasmの抽出。公開descriptorだけを信用せず評価器を再生成してbyte一致を確認する。旧SCC解析の未対応は防御成功に数えず、未知stateを毎回任意の環境として量化する新解析を実施した。'),
'research/novelty-analysis.md':('2026-10-23追補：有限収束分類と切替の先行性','[読了範囲付き比較](boolean-feedback/prior-art.md)。Boolean nilpotent dynamics、T-functionの合同保存、切替Boolean networkの安定性は既知。今回の普遍補正器の有限分類とcompiler接続則は構成候補として保存するが、同一先行技術の不存在・進歩性は確立していない。共役でないことを特許性と同一視しない。'),
'research/experiments.md':('2026-10-23追補：Boolean補正器3段階','[再現手順](boolean-feedback/README.md)と[集計](../results/invention-20261023/boolean-feedback-report-v1/report.md)。bitwise主179,466、word主194,502、切替主102,552呼出しで不一致0。各回復版・SMT・WABT・任意scratchを別集計した。wordは元版約237–266倍、切替版は固定補正約3.5–3.7倍の実行費用。全数分類と実binaryの効果を分離して報告する。'),
'research/research-gap.md':('2026-10-23追補：局所的な収束証明が回復を助ける問題','非共役の更新則に変えても、小SCC消去、元の算術部分式抽出、外部stateを量化した意味上の小部分探索で等価コードを得た。[切替実験](boolean-feedback/coupled-results.md)では依存graphを大きく循環させても、この最後の経路が残った。任意外部状態に安定する小群という生成側の正当性条件が、解析側の分割条件にもなる。一般の難読化不可能性ではなく今回の構成上の限界。'),
'research/literature-review.md':('2026-10-23追補：Boolean dynamicsと切替系','[書誌、読了範囲、評価未確認の区別](boolean-feedback/prior-art.md)を追加。Gadouleau/Richard（TCS2016）、Anashin/Khrennikov/Yurova（DCC2014、preprint2011/2012）、Li/Pang（Automatica、DOI2023）、F. F. Li（Neurocomputing2014）を照合した。sandpile/abelian networkは既知計算原理との近さを早期確認し、追加実装済み発明とは扱わない。'),
'paper-draft.md':('2026-10-23追補：非共役な残差補正と任意切替','**Abstract / Motivation.** 可逆な符号化に依存しないH=F XOR N(s XOR F)を検査した。全2^21個の3bit補正器を全128個の三角Fで分類し25,968個を得た。これは有限の構成知見であり一般次元の新規性の証明ではない。\n\n**Proposed Method / Implementation.** 最大3語のbitwise群、合同保存な3演算のi32持上げ、任意切替に安定な補正器族を使う群間結合の3段階を実Wasmへ実装した。元F・群境界を配布しない。切替族は136個のrank証明を別検査した。\n\n**Evaluation.** bitwise主179,466、word主194,502、切替主102,552呼出しが一致。word全6条件は公開式から26–37msで回復。切替版の大きいSCCに旧解析器は未対応だったが、環境stateを量化した意味上の小部分探索で全6条件を0.05–0.85秒で回復した。切替は同じ新解析器で固定版の約3倍の解析費用、約3.5–3.7倍の実行費用。\n\n**Discussion / Limitations / Conclusion.** 群境界の消失は小さい収束部分の消失ではなかった。3小関数・1seed、独自解析器の結果であり、WASMixer等への同一費用比較や実用program一般の主張はできない。先行理論との独立性も未確立のため主特許候補には採用しない。研究全体は継続する。[実装](research/boolean-feedback/README.md)、[結果](results/invention-20261023/boolean-feedback-report-v1/report.md)。')}
for file,(title,body) in entries.items():
    p=ROOT/file;text=p.read_text(encoding='utf8')
    if title not in text:p.write_text(text+'\n## '+title+'\n\n'+body+'\n',encoding='utf8')
p=ROOT/'README.md';text=p.read_text(encoding='utf8');notice='2026-10-23追補：[非共役なBoolean残差補正](research/boolean-feedback/README.md)を3段階まで実装・実験した。普遍補正器25,968個の分類と整数持上げの論証を得たが、bitwise・word・切替版はいずれも適応解析で回復。切替版の解析負担増は約3倍、実行増約3.5–3.7倍で主特許候補には不採用。[実測と再現](results/invention-20261023/boolean-feedback-report-v1/report.md)を保存し、別原理の研究を継続する。'
if notice not in text:p.write_text(text.replace('# webassembly_obfuscation\n','# webassembly_obfuscation\n\n'+notice+'\n',1),encoding='utf8')
p=ROOT/'research/novelty-status-20261023.md';text=p.read_text(encoding='utf8');title='非共役なBoolean補正器の追加結果'
if title not in text:text+='\n## '+title+'\n\n[実装・実験](boolean-feedback/README.md)。bitwise、word、任意切替族を用いた結合の3段階を検査し、全て等価コードへ回復できた。具体的な有限分類・持上げ・切替安全性の知見は保存するが、主特許候補は未確立。特に任意外部stateに安定する小群が公開Hからも抽出できることが、新たな不採用理由である。\n'
text=text.replace('6%使用（約94%残）','10%使用（約90%残）');p.write_text(text,encoding='utf8')
print('Integrated',len(entries),'research documents and status/readme')
