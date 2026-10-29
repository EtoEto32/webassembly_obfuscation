# K：非破壊の状態識別プローブを生成する復元検査（事前計画）

2026-10-24。特許ではなく修士研究の候補。新規性は未確立。Jの主機構がWeaveと重なったため、**状態を可逆化する原理から、状態差を非破壊に識別して復元契約を検査する原理へ変更**する。

## 問いと仮説

Wasmのmemory bytesとglobalsが同一でも、容量、table内容、segmentのdrop状態は異なり得る。snapshot/resetの検査に対して、Wasm命令の意味から作る非破壊observerを使うと、単なるbyte一致や通常の後続入力が見落とす差を、状態を壊すprobeなしで分類できるか。

特に非空segmentに対する `init(dst=0, src=1, len=0)` は、宛先が0長でも存在すれば、保持中は成功、drop後はtrapする。0長操作が範囲検査を行うこと自体は仕様・既存testに明記され、発明とはしない。自動挿入、state descriptorの合成、reset境界での比較、実APIでの反例確認という検査手順の有用性を評価する。

## 分けて検討した3方向

|候補|原理|主な反証・判断|
|---|---|---|
|J|物理stateを残して論理stateへ復元操作を写す|Weaveと主要機構が重なり、主案から降格|
|K|破壊を伴わない命令文脈でhidden stateを識別する|仕様testの単なる自動化なら学術的新規性は弱い。実対象への一般性と独立oracleを検査|
|L|次のrequestで必ず上書きされる範囲を静的証明しresetを省く|既存definite-assignment/secure reuseとの距離が弱い。StackArmorの論文を先に比較し、この段階では実装に進めない|

## Kの契約

入力は実 `.wasm`。閉じたcore moduleのmemory/table/numeric globalsと非空passive segmentsを列挙し、追加observer exportsとmanifestを生成する。元のindexを保持し、追加observerを既存関数が呼べないよう末尾へ追加する。shared/imports/GC/外部資源は当初対象外。observerを追加したことによる最適化・情報公開の変化はテスト専用instrumentationとして明示する。

segmentのbytesはimmutableで、有効長は元長または0。空segmentのdrop前後はこのモデルで観測同値なので異常と数えない。active/declarativeは初期状態から空。memory/table長、memory全bytes、numeric globalのraw bits、tableのfunction index対応、segment有効性を比較する。通常のnumeric APIから観測できる差の証明とは区別し、必要なら元APIの後続呼出しで確認する。余分なobserverで初めて露見する差をそのままセキュリティ上の漏えいと呼ばない。

## 実装・実験の順序と成功条件

1. WABTで検証済みbinaryへobserverを挿入しNodeで実行する。segment probeが成功/trapの両方でbytes/global/table/segmentを変更しないことを反復・後続initで検査する。
2. 境界状態（0page、空segment、drop再実行、active/declarative、table、float raw bits）、複数segment、生成した状態列を使う。元binaryとinstrumented binaryの元API動作も比較する。
3. fresh instance、正しいJ、Jの誤実装対照、bytesのみの復元を比較。これは自作mutantへの感度であり既存製品の不具合数とはしない。
4. Node/Wasmtime等の別engine、最適化前後を比較する。未対応、拒否、trap差、値差を分離する。
5. 生成費用、追加size、probe費用、検出できるstate種別を記録。必要に応じて保存式のbyte oracleと比較する。
6. 公開spec testと最近接生成器WEST/WASMaker、checkpoint test（Weave）と直接比較し、単なる既知testの列挙以上の貢献を主張できなければ主案には採用しない。

数学的には、限定モデル内の構成要素一致が以後の観測同値の十分条件になることを論証する。hash一致は衝突し得るので全入力証明に使わず、正当性試験ではbytesの直接比較を行う。リソース枯渇・タイミング・stack活性状態はこの命題に含めない。

段階2の変更理由：公式table_initテストへの適用で26moduleをmulti-tableだけの理由で除外したため、full observerを最大4個のprivate funcref tableへ広げる。別発明とは数えない。Jとの統合用numeric profileはfunction identityを比較できないため、完全なstate一致を証明したとは扱わない。公式テスト末尾のGC構文はWABTが解釈できず、未読込み区間を記録して分離する。
