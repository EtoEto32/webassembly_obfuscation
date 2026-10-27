# Kの検査契約と信頼境界

2026-10-24。検査対象は誤りを含み得るWasm reset/checkpoint変換である。悪意あるruntimeから完全な証拠を得る仕組みではない。検査host、WABTのvalidation、実行engine、入力の固定hashを信頼する。初期のfull observerは閉じたnumeric interfaceとnonshared stateを対象にし、外部参照を注入しなかった。

現在の条件合成では元API・公開resourceとprivate resourceを区別する。外部書込み禁止が既定値だが、[host拡張](guard-environment-results.md)では、元からexportされたmemory/tableへ同じ任意値を両側へ書く操作も入力に含める。hostは停止中の非共有stateだけを操作し、grow・imports・再入・時間・OOMは扱わない。table値は対応付けた関数identityであり、外部参照を呼び出す効果の同値性は検証しない。実行oracleは純粋定数関数だけを呼び、任意の利用者関数へその照合方法を適用しない。

以下の契約を区別する。

別の[同期void import profile](guard-import-proof.md)では、hostのread/write summaryを明示して内部呼出し境界を扱う。summaryはtrusted入力で、host例外・再入・grow・外部I/Oは含めない。元import付きbinaryの読取りに対応したことは、任意host programを解析したことを意味しない。指定された継続offsetを使う場合も、復元PC/stackとの対応は別の前提である。

`writes: public`はfootprint内の全公開cellへの**必須共通上書き**であり、一般的なmay-write許可とは違う。省略・部分上書きを含む場合は`writes: may-public`を選ぶ。[両契約を区別する実験](guard-import-may-results.md)では、全上書きで消える差が任意subsetでは残る。左右のmaskと代入値を共通にする環境モデルであり、別々の独立した非決定的host出力まで同一にする要求ではない。

|契約|比較するもの|それだけでは言えないこと|
|元entry|返却値/成功/trapと公開memory|private stateの同一性、別API列での一致|
|元guest store|論理memory全bytes/長さ、global bits、table参照、segment寿命|active stackや変換器の内部metadataを含む完全復元|
|元API列|限定profileでの遷移閉包、または保守的な十分条件|未対応命令・imports・shared stateを含む一般同値性|
|物理snapshot|payload bytes/control metadata|再実行を許す契約での意味的な正否|

probeで追加された観測からのみ判明する差は、元API利用者への脆弱性や漏洩に読み替えない。資源枯渇・時間・stack limitは契約から除き、実行時に観測したtimeout等は別分類で保存する。試験通過は全入力証明ではない。

full observerのcanonical exportsは同じinstance内で関数identityを対応付ける。Weaveはwrapperを挿入するのでこの規則が合成できない。directory版は元関数を追加tableに配置するが、このtableの対応が正しいという追加前提を持つ。同じ誤りがguest tableとdirectoryへ同時に入ると、index labelが保たれたように見える可能性がある。元APIの独立比較を併用し、directory単独を完全な変換検証と呼ばない。

Weave restore直後の物理tableはまだshadowから再構成されていない。directoryによるfull state検査はresume完了後に限定する。numeric segment probeをcheckpoint時に使う実験は、snapshotを先に取得し、観測用と再開用のinstanceを分ける。observer wrapperが再開metadataを書き換える交絡を除くためである。
