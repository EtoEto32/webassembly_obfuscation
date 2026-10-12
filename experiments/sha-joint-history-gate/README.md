# SHAの作業状態・展開状態を24語の履歴に統合する案

> 現行目標での再評価（2026-10-12）：以下は旧評価条件を含む履歴。
> 容易な復元、攻撃に対する優位性の欠如、汎用Wasm非対応は現在の棄却理由ではない。
> [座標変更の証明と判定の修正](coordinate-proof.md)：共役表示だけでは新規性を否定しない。
> 既知のA/E再帰の代入・変数消去を超える具体的差分が未提示のため、新規性未確定・採用保留。

## 1. 状態：Inconclusive

2026-10-12。研究目標は未達で、状態はactive（継続中）。新規性は未確定で、既知の再帰からの構成との差分が不足しているため採用保留。短い明示復元式があること自体は棄却理由にしない。新しい難読化変換器として完成したという主張はない。

## 2. 達成事項

SHA-256の作業8語とrolling message schedule 16語を、24個のA履歴へ置き換える実行規則を定義した。ラウンド0〜23は通常のprologue、24〜63は24履歴だけから次のAを計算する。パディング・64ラウンド・feed-forward・複数ブロック連鎖を含むPython試作を実行した。過去の任意u列や8ラウンドだけの結果とは異なり、今回の対象はSHA全体の実際の入力である。

全観測地点から元の作業状態と展開語を復元でき、状態統合だけでは保護機構を生まないことをこの具体案で確認した。

## 3. 未達事項

必須条件で未達なのは、独立した新規原理の根拠と、新方式のWasm SHA適用・検証。汎用変換器、攻撃比較と優位性、コスト・最適化後の残存性は現行目標の必須条件ではない。Pythonによる完全SHA検証と、要求されたWasmの新方式適用を区別する。

## 4. 変換式と意味保存

全語32ビット、加減算はmod 2^32。A_j,E_jはラウンドj後のa,e。Q(x,y,z)=Σ0(x)+Maj(x,y,z)。通常式から次を得る：

```text
E_j = A_j + A_(j-4) - Q(A_(j-1),A_(j-2),A_(j-3))
W_j = A_j - Q(A_(j-1),A_(j-2),A_(j-3))
      - E_(j-4) - Σ1(E_(j-1)) - Ch(E_(j-1),E_(j-2),E_(j-3)) - K_j
```

境界i（i回更新済み、次がラウンドi）でH[k]=A_(i-1-k), k=0..23を保持する。上式でHから得るE_(i-1-k)をe(k)、W_(i-1-k)をw(k)と略す。w(k)はH[k]〜H[k+8]を使う。従ってk=0..15のすべてが24履歴から復元できる。

通常のmessage scheduleを代入して：

```text
Wnew = σ1(w(1)) + w(6) + σ0(w(14)) + w(15)
Anew = e(3) + Σ1(e(0)) + Ch(e(0),e(1),e(2)) + K_i + Wnew
       + Q(H[0],H[1],H[2])
Hnew = [Anew] + H[0:23]
```

これをi=24..63で実行。advanceには元の入力block、通常状態の8ワードstate、W配列を渡さない。prologueのW0..23はその関数から戻る際に破棄する。最終作業状態はH[0:4]とe(0)..e(3)で得る。

初期prologueで履歴は実際のA23..A0に一致。上のW復元式で本来のWの値が得られ、元のschedule式とround式へ代入すれば次のAも一致する。これを帰納的に繰り返し、最後のfeed-forwardによりcompression出力が一致する。paddingとchainingは標準のまま。これは代数的説明でありSMT・機械定理証明ではない。

この24語は一般のjoint stateに対する可逆な座標変更とも解釈できる。直前16個のWが与えられれば通常roundを16回逆算でき、その開始状態を既存の8語A履歴へ変換し、16回のforward更新で24語を構成できる。ただし本実験は任意768ビットjoint stateの全数検査を行っておらず、実際のSHA入力による状態を確認している。

## 5. 先行研究・新規性

2026-10-12に [Dobraunig, Eichlseder, Mendel, CRYPTREC報告 (2015)](https://www.cryptrec.go.jp/exreport/cryptrec-ex-2401-2014.pdf) のmessage expansion式(1.1)、A/E式(1.2),(1.3)、SHA-256を定義する§1.3を再確認した。24語への統合式が同資料にそのまま載るとは主張しない。しかし基礎となるA/E再帰とscheduleは既知で、本案はそれらを代入・消去した具体的な状態表現変更である。単に二つの既知再帰を統合したことでは、要求された独立した原理を支持しない。

|比較項目|判定|
|---|---|
|数学的な原理|既知のSHA再帰の代入と変数消去|
|表現体系|以前のA履歴をscheduleの保持にも利用|
|状態変換|明示的な復号関係を持つ履歴座標変更|
|依存関係|24ステップへ広がるが、元のWを生成式内で再構成している|
|困難性の原因|復元式が短く、保護効果は確認できない|
|一般化|本試作はSHA-256専用。任意Wasm変換規則なし|

検索語：`"SHA-256" "obfuscation" "state"`、`"obfuscation" "message schedule"`、`"obfuscation" "ARX" 2026 new`、`"SHA-256" "24" "recurrence" message state`、`"SHA-256" "eliminate" "message schedule"`。一致する名称が見つからないことを新規性の証拠にしない。検索で出たSHAの逆算に関する未検証プレプリントは根拠に採用しない。

方向選別時に [Pawlowski, Contag, Holz, Probfuscation TR-HGI-2016-002](https://pawlowski.dev/assets/tr16_probfuscation.pdf) の要旨、§2–4冒頭も確認した。確率的制御フローと動的解析のモデルの資料であり、この24語式の先行実装ではない。別のstate-space preprintの取得は502で失敗、本文確認済みに数えない。回転符号化の検索も行ったが、具体候補として採用・実行していない。

## 6. 再利用

A：baselineのinputs.bin/json、sha.jsのIV/K定数、Python 3.12.14。入力bundleのSHA256を実行時に照合。B：sha-history-gate/check.pyの回転、Q、通常roundを再利用し、今回の出力をhashlibで照合。C：sha-history-gateの復号式とsha-prefix-reachabilityの実到達証人の基準。保存済み検証件数を今回へ加算していない。

## 7. 実装・正確性

protocol.jsonで入力を事前指定。empty/abc/long-known、padding境界を含むlengthケース、511/512/513byte、baselineから条件を満たす最初の16乱数入力。計36メッセージ、222ブロック。

- 全36最終digestが保存済みbaselineおよびPython hashlibと一致。
- 境界i=24..64の全9,102地点で8 working wordsと直前16 schedule wordsが通常実装に一致。
- 計218,448語の復元照合。状態数・語数は別指標。
- 復元W24の1ビットを毎blockで反転した負例では、36件すべての最終digestが不一致。

normalとcandidateはprologueおよび基礎関数を共有するため、内部状態について完全に独立した2実装という表現は使わない。完全digestは外部のhashlibと比較した。新しいWasm実行やSMT検証は実施していない。

## 8. 復元者・比較

復元者は24履歴の配列順序、境界番号i、公開SHA定数と方式を知り、履歴を観測できる。observerに元state、W、平文は渡さない。プロセス隔離した盲検ではなく、コード上の情報分離。未知バイナリから境界・配列位置を発見する処理は実装していない。

復元者は§4の式を計算するだけで全joint stateを得る。しかも候補advance自身が必要な4個のWを同じwword関数で再構成する。本結果は独立に発見した高度な攻撃ではなく、生成式に復号が残ることの実際の入力による確認である。強い観測前提の初期否定試験であり、既存方式との公平な勝率比較を済ませたとは言わない。

## 9. コスト・最適化

Wasmコードサイズ、処理時間、wasm-opt残存性は未測定。24語保存は通常の8+16語と同数。次状態生成中にWを復元する追加計算があるが、定量的な実行オーバーヘッドは測っていない。Python試験は約1.95秒で終了し、これをWasm性能指標にはしない。

## 10. 改善判断

旧A履歴案は任意u=K+Wを外部から与えた。今回はmessage scheduleも状態へ統合し、SHA全体の後半40roundを履歴だけで更新した。joint stateの復元成功による旧棄却は撤回する。現在の採用保留の理由は§5の具体的な既知再帰の代入・変数消去を超える差分が未提示なこと。履歴長やround境界だけの変更を新規性の根拠にしない。

## 11. Before/After

sample ID SHA-JOINT-HISTORY-24。実行したBeforeはcheck.pyのnormal、Afterはprologue+advance+最終復号。§4が変換箇所の式対応。Python試作であり、生成器が出したWATサンプルではない。汎用変換器、Wasm After、最適化後コードは未作成。

全履歴と復元値はartifacts/observations.jsonl.gzに保存。各行はcase、block、boundary、history、recovered_state、recovered_W。Pythonのgzipで展開できる。全通常トレースは入力から再計算し各行で照合する。cases.jsonに入力位置、期待値、実際のdigest、破損版digestを保存。

## 12. 保存場所・再現

本ディレクトリのprotocol.json、check.py、artifacts一式。元コード・入力bundle・計画・生成物のSHA256をresults.jsonに保存。リポジトリルートから新しい出力先へ：

```powershell
.tools/runtime-analysis-py312/Scripts/python.exe experiments/sha-joint-history-gate/check.py experiments/sha-joint-history-gate/replay-artifacts
```

標準ライブラリのみ。既存出力は上書きを拒否。探索は本規則1件、20分枠、実行60秒以内に限定。既存CSEC資料・過去成果を変更していない。

## 13. 限界・残る課題

SHA全体の計算式を変更しても、その変更が独立した難読化原理であるとは限らない。未解決なのは、既知の再帰を代入して得た構成と、本案独自の変換規則との差分である。全履歴方式・全状態符号化の不可能性を示すものではない。復号の困難性や攻撃上の優位性は採用条件にしない。
