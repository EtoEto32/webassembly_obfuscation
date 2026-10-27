# コピーの情報損失に適合する表現：事前計画

2026-10-22。前区間は状況説明のみでno progress。本区間は既存prefix-repairの「入口保存値のみから修復」という制約を外し、出口の現memoryを副情報として利用する仮説を検証する。独立した新原理の候補数には加えない。新しい主発明の確立という目的は維持する。

仮説：コピーprefix P が失う入力部分空間を可逆表現Bが保存すれば、Pをnative実行した現memoryから、B P B^-1 の結果を復元できる。全prefixをこの条件に適合させれば、入口から保持する値が不要となる。出口修復自体の一時値は必要であり、zero memory/register overheadとは主張しない。

対象はprivate memory32、固定1page、2..64 byte、1..16個の定数・正長copy列。run(fail)は指定したcopyを範囲外にし、digestは復号したbyte列のFNV。元のprefix-repairと同じ閉じた実binary profileを厳密に認識する。任意アプリ・動的copy・共有memory・host callback・memory growは非対応。

対照は未変換、同じBの各copy修復(eager)、入口共有基底保存(basis)、現memory修復(current)。badは正常出口だけを修復してtrap prefixを省いた意図的負例。行列を変えた比較を性能向上の根拠にしない。

成功条件は(1)全prefixの記号行列恒等式、全3bit状態の小モデル、実Wasmの値・trap・全page状態一致、(2)入口保存byte数の削減、(3)同じBのbasisより実行中央値が10%以上改善するケースがあり悪化も報告、(4)独立した保護優位は方式既知の回復費用を別に測る。費用削減だけで保護性能・特許性を認定しない。

旧binary-only回復器をソース・生成manifest・queryを与えずそのまま試す。復元できたなら新規保護方式としての主採用はしない。初期のparser不足・tool crash・timeoutは耐性に数えない。範囲外copyが書込み前にtrapするWasm仕様に依存し、trap後のdigestと次回runも検査する。

3つの固定copy構造、2 seeds、raw/O3を使うが、実アプリ3個とは数えない。境界byte、walking byte、seed付きrandom状態・反復操作を検査する。正常runをWasm内部loopで測り、warmup、3 fresh process、7 batch、10ms以上を目安に校正。サイズ・64KiB memory・process RSS・変換時間を保存。性能では未計測のtrap経路への一般化をしない。
