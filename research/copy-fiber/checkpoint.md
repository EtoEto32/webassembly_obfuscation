# 継続地点 2026-10-21

この区間はprogress。copy-fiberの実Wasm変換、全SHA照合、binary-only解除、性能、
負例、別engine、byte再現を実行した。全processは終了している。

- 主10条件：圧縮2,620比較、全SHA410比較、診断memory160件、不一致0。
- 回復20条件：圧縮5,240比較、全SHA820比較、不一致0。同じ262入力/41messageを使用。
- 全10入力binaryが同じ1,881演算DAGへ回復。byte列は4種類であり意味の一致と区別。
- 18fresh process：非線形native1層はplain約23.47倍、素朴repair比約3.12%時間減。
- 4,096小モデル、100逆変換、4誤変換実例、3非対応拒否、10主byte再現、6WABTprobe。
- 主監査はaudit-v3。v1/v2の失敗sourceと理由を保持。既存の他系列のpinは変更しない。

gを非線形にして公開状態APIを消しても、各read/writeを跨ぐ相殺は機械的にできた。
次の新案では安い復号境界を横断されない具体機構を考える。単なる多層化、hidden API、
inline、一般の共役融合を別発明と数えない。EOCの非線形共役・BDD表現は確認済み。
今回の主案採用は見送り。有限環残差方式の限定した構成的提案は保持し、goalはactive。
