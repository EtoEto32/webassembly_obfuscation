# トラップ前の書き込みを保持する領域変換：事前設計

2026-10-12。新規性未確定の具体的な規則を試す正しさゲート。独立研究であり、CSEC原稿は変更しない。

## 変換規則

入力はi32の直線SSA領域。加算・乗算・XOR、unsigned除算、単一memoryのload32/store32を扱う。アドレスはi32 unsigned、offset=0、非共有の1ページmemory。外部呼出し、memory.grow、atomics、例外、ループ、分岐、複数memory、公開globalは対象外。

1. 領域の演算を元順序で評価する。ただしstoreはアドレス・値・有効フラグをlocalへ保存する。
2. 最初の不正メモリアクセスまたはゼロ除算をfaultへ記録する。以後のstoreは無効。除算はゼロ時のダミー除数1を使用し、不正loadは0を返して、その場でtrapしない。
3. loadは元メモリに、先行する有効storeをバイト単位で重ねて評価する。非整列かつ部分的に重なるstoreを扱う。
4. 領域末尾で有効storeの各byteについて、後続の有効storeが同じbyteを覆う場合はそのbyteのcommitを省く。残ったbyteを逆順でcommitする。アドレスごとに最終の有効な書き込みだけが残る。
5. faultがあれば対応する種類のWasm trapを起こす。なければ元の返り値を返す。

正常時だけでなく、trapで戻った際に外部から読めるmemoryも保存する。JavaScriptのスタックトレース文字列、実行途中のデバッガ観測、時間・メモリ使用量は保存対象外。importや共有メモリを許すとcommit延期の間に他者が旧状態を観測できるので、この規則の適用対象にしない。

## 比較

- native: 元の順序のWasm命令。
- guarded: 同じ順序で明示的な範囲・ゼロ検査をする自作対照。
- deferred-ordered: faultを遅延し、ログを元順序でcommitする。
- deferred-coalesced: 上記規則で重なったbyteを統合する具体候補。

guardedは著者実装ではない。deferred-orderedはbyte統合を除いた版で、意図的に不正な対照ではない。全版が同じ定義済み挙動を持つ必要がある。

## 正しさの説明と反証

最初のfaultより前について、loadのforwardingが元のmemoryを再現するという帰納的不変条件を置く。有効storeはそのprefixにちょうど一致する。各byteで最後の有効storeだけをcommitしても、prefixを逐次適用した最終memoryに一致する。faultの種類は最初のものを保持する。これらの条件を破る入力が一つでもあれば変換を修正する。有限個の入力によるテストを全入力証明と呼ばない。

独立JSインタプリタを基準に、正常返り値、trap種類、64KiB全memoryを比較する。アドレスの境界、非整列・部分重複・完全重複、複数fault、先行storeで後の除数やアドレスが変わる例を含める。raw/O2の両方を確認する。

## 研究上の仮説と未検証点

保護候補は元の書き込み境界とその並び。統合後の物理的なstore列だけから元の順序が直接読めなくなる可能性がある。ただしlocalログと有効フラグを解析すれば再構成できる可能性が高い。単に最終memoryへの書き込み数を減らしただけなら最適化であって、新しい難読化とは認めない。

全バイナリと任意入力・内部計測を持つ解析者が、元の有効store列の意味を再構成できるかが次の評価対象。今回の段階ではその復元器・性能比較は未実装。適切な復元成功条件と具体的な先行例との差を確定する前に、難読化の有効性を主張しない。

## 関連する研究

- Chenほか、BOSH / Control Flow Obfuscation with Information Flow Tracking、MICRO2009。著者Bo Huangが掲載した全文の§1と§4.1周辺を確認。例外tagの伝播と違反時の制御移動を難読化へ利用する。今回のソフトウェア上のcommit規則と同一とは未確認。著者コード・Itanium実験は未実行。https://www.researchgate.net/publication/221005352_Control_Flow_Obfuscation_with_Information_Flow_Tracking
- Constantine、CCS2021。§4.2.5と§4.2冒頭、付録の例外に関する前提を確認。decoy経路の不正除算対策があり、元プログラムはerror-freeを仮定する。Wasmの正規のtrap前memory保存を評価したとは言わない。https://download.vusec.net/papers/constantine_ccs21.pdf
- LOKIの固定コードにおけるメモリ式の展開制限は既存control-fusion-source-auditを参照。未対応機能を増やしただけで新規性としない。
- Sentinel schedulingのstore bufferと例外延期は検索で見つかった。著者本文の必要節をまだ取得・確認しておらず、この比較は未完了。

検索語: obfuscation deferred exceptions / obfuscation transactional memory / sentinel scheduling deferred exceptions stores speculation / obfuscation store coalescing。

適用範囲の制限は研究全体の目標縮小ではなく、この具体案の最初の意味保存試験の範囲。新しい変換原理が確立したとは扱わない。
