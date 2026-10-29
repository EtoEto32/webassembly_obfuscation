# 先行技術と採否

調査日2026-10-23。最も近いのはRNCデータ難読化であり、moduliの変更を新発明には数えない。

|資料|確認範囲・位置付け|今回との関係|
|---|---|---|
|Biniam Fisseha Demissie, Mariano Ceccato, Roberto Tiella, *Assessment of Data Obfuscation with Residue Number Coding*, SPRO 2015。著者公開[論文](https://profs.scienze.univr.it/~ceccato/papers/2015/spro2015.pdf)、[公式programme](https://spro.aspire-fp7.eu/spro2015/)、[機関書誌](https://cris.fbk.eu/handle/11582/300566)|会議workshop論文の著者版。Abstract、§II–III、結果・関連研究・結論を読んだ。Clangによる二成分の表現、対応演算の成分実行、非対応演算の復元再符号化を記述。license checkでは変数追加当たり1.19KB・8.85msの回帰係数、MD5の実行時間では有意な相関なし。human attack評価は将来課題。著者実装は未実行|RNC原理もrepairの構成も既知。著者の実験条件・測定器は異なり、今回の倍率と性能順位を比較できない。今回の反例を著者実装へ帰属しない|
|Dhananjay S. Phatak, *Residue Number Systems Methods and Apparatuses*, [US20110231465A1](https://patents.google.com/patent/US20110231465A1/en), 2011-09-22公開、priority 2010-03-09|公開特許資料。書誌、RNS並列channelの説明、overflow detection節の一部、claim 1–2の抜粋を確認。全請求項の精査・法的状態の判断は未実施|剰余系のreconstruction・overflow処理自体は既知。今回のWasm規則と同一の請求項を確認したという意味ではない|
|Andrej Spielmann, Viktor Kuncak, *Synthesis for Unbounded Bit-vector Arithmetic*, IJCAR 2012、DOI [10.1007/978-3-642-31365-3_39](https://doi.org/10.1007/978-3-642-31365-3_39)、[著者PDF](https://lara.epfl.ch/~kuncak/papers/SpielmannKuncak12SynthesisUnboundedBitvectorArithmetic.pdf)|導入と§4の二走査transducer構成を確認。unbounded integerの線形算術・bit操作を扱う。実装未実行|このturnの初めに検討したbit直列carry案はrepositoryのoperand-rebasingとも重複したため別案として採用しなかった。RNCの新規性根拠に転用しない|

RNC論文が引用するZhu/Thomborson 2005 *A provable scheme for homomorphic obfuscation in software security*、Zhu/Thomborson/Wang 2006 *Obfuscate arrays by homomorphic functions*は今回本文未読の探索lead。本文を読んだ文献には数えない。

今回の独自作業は、明示したWasm移植規則の反例、二修正の実装、公開binaryだけを使う射影器、測定・再現物である。これをRNC自体の発明・新規な環の定理・著者実装の誤りと呼ばない。最大のReject理由は、生成規則が既知の表現変更であり、追加の保護効果も確認できないこと。主特許候補には不採用。特許性の判断を得たとは扱わない。
