# 先行技術との照合

確認日2026-10-23。法的な特許性・権利範囲の判断ではなく技術比較。未読箇所を推測しない。

|資料|確認した範囲|今回との関係|
|---|---|---|
|Paul Marion Hriljac, *Systems and methods of source software code obfuscation*, [WO2012040383A1](https://patents.google.com/patent/WO2012040383A1/en), 公開2012-03-29、優先日表示2010-09-24|書誌、説明0048–0057、0066–0074、0078–0086。公開公報であって査読論文ではない|非線形な多変数座標変換とその合成・簡約が直接近い。今回の違いとして調査すべき部分は有限回flushによる初期・出力codecの不要化と生成条件に限る。これだけで非自明と判断しない。公報の一般整数上の困難性記述を、有限32bit上の保証として流用しない|
|Adrien Richard, *Nilpotent dynamics on signed interaction graphs and weak converses of Thomas’ rules*, Discrete Applied Mathematics 267,160–175,2019, [出版社](https://www.sciencedirect.com/science/article/pii/S0166218X19302355)、[arXiv:2201.08596](https://arxiv.org/abs/2201.08596)|査読掲載情報、要旨・導入の定義。全証明は未読|有限回収束する状態系、複雑な依存グラフと単純な力学の併存は既知。今回のWasm変換が記載されているとは確認していない|
|Alexandre Mauroy, Jorge Goncalves, *Linear identification of nonlinear systems: A lifting technique based on the Koopman operator*, IEEE CDC2016, DOI[10.1109/CDC.2016.7799269](https://doi.org/10.1109/CDC.2016.7799269)、[arXiv:1605.04457v2](https://arxiv.org/abs/1605.04457v2)|査読会議書誌と要旨。本文・数値評価未読|観測空間へ持ち上げた線形同定という一般原理が先行。こちらの解析器は有限Boolean環で係数を完全一致させる。既存研究の評価数値を再現したとはしない|

追加探索で *Linear Obfuscation to Combat Symbolic Execution*（Wang, Ming, Jia, Gao, ESORICS2011, DOI10.1007/978-3-642-23822-2_12）、*Code obfuscation against symbolic execution with mixed Boolean-arithmetic permutation*（Wangほか、オンライン2026-09-23、DOI10.1177/0926227X261470417）の書誌・要旨を確認した。本文未取得なので具体的な解除耐性や差分は断言しない。

検索語は `obfuscation finite time convergent dynamical systems nilpotent polynomial code`、`code obfuscation polynomial observables Koopman invariant recovery nonlinear coordinate patent`、`code obfuscation self-stabilizing` 等。検索で完全一致が見つからないことは新規性の証明ではない。

**判断**：可逆変換・合成の展開自体は先行技術。初期化不要化は今回説明・実装できた具体的性質だが、既存手法からの非自明な差と有利な費用対効果を確立していない。rank条件を満たすものも方式既知の二次解析で回復した。主特許候補には採用せず、失敗条件と比較コードを次の設計に引き継ぐ。
