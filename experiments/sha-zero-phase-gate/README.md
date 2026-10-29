# ゼロ入力による位相正規化の実際のSHA反例

## 1. 最終状態

2026-10-12。**Inconclusive。新規アルゴリズムの発明という研究目標の状態はactive（継続中）・未達。** 位置依存の復号を許す具体的な規則を検査し、この規則では共通更新を作れないことを確認した。新しい難読化原理として採用しない。

## 2. 達成事項

前回の文献監査で未確認だった「相殺する符号化から共通ハンドラが得られるか」を、ゼロ入力遷移の累積逆写像という具体的な規則で検査した。異なる64byte入力2件を構成し、同じ符号化状態・同じ現在入力語から異なる符号化次状態になる反例を、Pythonおよび既存のraw/O2観測Wasmで確認した。

## 3. 未達事項

独立した原理を持つ難読化変換器、SHA全体への新方式適用、既存方式との公平な攻撃比較・優位性は未達。ここで実行したSHAは既存の通常実装とその観測版であり、新しいAfterではない。

## 4. 変換規則と反例

Sは8個の32bit語。T_i,wは標準SHAラウンドiにW_i=wを与えた置換。全加減算はmod2^32。境界8を基準に

```text
P_8 = id
P_(i+1) = T_i,0 ○ P_i
E_i = P_i^-1
z = E_i(s)
U_i,w = P_(i+1)^-1 ○ T_i,w ○ P_i
```

と定義する。D_i=P_iなので復号は位置に依存する。U_i,0=idは必ず成立する。しかし位置を受け取らない共通U(z,w)が得られるためには、非ゼロwでも全位置のU_i,wが一致しなければならない。

H_w(a,b,c,d,e,f,g,h)=(a,b,c,d,e,f,g,h+w) と置く。WはSHAのT1へ加算されるので T_i,w=T_i,0○H_w。従って

```text
U_i,w = P_i^-1 ○ H_w ○ P_i
```

となる。ゼロ入力更新を消しただけでは、データ入力の作用とP_iの交換可能性は得られない。今回の具体的な反例は

| 境界i | z | w | U_i,w(z) |
| --- | --- | --- | --- |
| 8 | (0,0,0,0,0,0,0,0) | 1 | (0,0,0,0,0,0,0,1) |
| 9 | (0,0,0,0,0,0,0,0) | 1 | (0,0,0,0,0,0,1,4294967295) |

P_8=idなので1行目は直ちに従う。P_9=T_8,0を用いて逆算すると2行目になる。固定uに対する逆ラウンド式は既存 `sha-phase-capacity/check.py` のinverseを再利用した。異なる次状態を同じ引数の決定的関数が返すことはできないため、**このE_iに対する**共通更新仮説は不成立。

実際の入力は、境界8をゼロにする既存prefix構成で最初の8語を求め、後半8語のうちW8又はW9だけを1にする。前者の境界8でz=0、後者の境界9でz=E_9(T_8,0(0))=0。正規パディングは次のブロックに入る。完全機械状態が等しいという主張ではない。

原式U_i,wを位置付きで実行すれば意味保存は成立する。棄却したのはiを無視できるという主張であり、元のSHA計算自体ではない。共通Dに基づく前回の259bit下界とは別の反例。

## 5. 新規性・先行研究

入口・出口表現の相殺による規則であり、独立した新規性は確認できていない。前回の `tmp/phase-encoding-source-audit/README.md` が本文確認した [Ranea and Preneel, SAC20](https://sacworkshop.org/SAC20/files/preproceedings/02-WhiteBox.pdf) の入出力符号化と比較する。

| 比較項目 | 判定 |
| --- | --- |
| 数学的原理 | 境界表現による共役・相殺 |
| 表現 | ゼロWの累積遷移を基準にした位置依存表現 |
| 状態変換 | U_i,w=P_i^-1 H_w P_i。通常の状態表現変更に還元 |
| 依存関係 | 位置依存性が入力作用へ移る |
| 解析困難性 | 未評価。共通更新という設計条件が不成立 |
| 一般化 | 任意入力族を持つ系では基準入力以外の作用も確認する必要がある |

今回の追加検索（2026-10-12）: `WebAssembly obfuscation 2026 novel transformation obfuscation paper` と `obfuscation computation pebbling recomputation data flow retiming`。[Proof-of-Theft, ECOOP2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol372-ecoop2026/html/LIPIcs.ECOOP.2026.25/LIPIcs.ECOOP.2026.25.html) は要旨・導入を確認したが、この規則の新規性や攻撃結果の根拠にしていない。既存docsにも記録があり、新発見として扱わない。A²-MBAの出版社本文は取得エラー、既存promba-width-auditに調査履歴もあったため検索スニペットから追加判断しなかった。再スケジュール案は既存temporal-cut-gateに記録があり、再実装しなかった。

## 6. 再利用成果

A（今回の限定用途）: `sha-phase-capacity/check.py` の逆式・PythonによるSHA全体の実装照合、`sha-phase-witness/build.py` のprefix、そこから参照されるSHA補助関数と標準定数。

A: `sha-phase-witness/artifacts` のbefore.wasm、capture.raw.wasm、capture.O2.wasm。元manifestのSHA-256とも照合して実行した。既存の640..735の観測領域を利用し、再ビルドはしていない。

C: 前回の文献監査と容量下界。一般的な自己同値符号化の新規性・攻撃効果の証拠には流用しない。

## 7. 実装と検証

protocol.jsonを実行前に保存。check.pyが構成・Python検査・manifest生成、verify.cjsがWasmを実行する。Node側にも逆式を記述し、Pythonが保存した符号化値を単に読み出すだけでなく、Wasmで観測した通常状態から再計算した。

- Python3.12.14: 2入力の完全SHAがhashlibと一致、ゼロWで恒等更新になる対照2件を確認。
- Node v24.15.0、V8 13.6.233.17-node.48: 3既存Wasm×2入力の完全ダイジェスト6件一致。Node cryptoでも入力から再確認。
- raw/O2観測版×2入力×境界8/9/10: 通常状態12件一致。
- 同一z・同一W・異なるznext: raw/O2の2条件で確認。同じ反例対であり、独立した2組ではない。
- 入力メモリ保存、beforeが観測領域を変更しないこと、実行ソースと依存物のハッシュを確認。

SMT未実行。実行検証は2入力のみであり、以前の531入力試験を再実行したとは報告しない。

## 8. 攻撃比較

復元攻撃ではなく、候補の共通更新条件の反証。未知Wasmからの境界認識・復号器発見は評価していない。plain/MBA/新方式の攻撃比較は未実施。

## 9. 性能・サイズ・最適化

新方式の性能・サイズは未測定。O2でも反例を確認したことは難読化機構の最適化耐性を意味しない。実行した3本は既存生成物であり、新しいビルド費用を報告しない。

## 10. 改善サイクル

共通Dを外すだけの抽象案から、ゼロ入力の累積逆写像を選ぶ具体的な規則に進んだ。基準入力ではすべて恒等更新になるが、非ゼロ入力の作用が位置ごとに共役されるため共通化に失敗した。固定w=0でのみ合成・評価すると、この不備を見逃す。

本則の入力数増加やWasm変換器化は行わない。次の候補には、入力族全体の条件を最初から課す必要がある。ただしこの条件を満たすだけで新しい難読化原理や攻撃の困難さが得られたとは認定しない。

## 11. Before/After

Beforeは `../sha-phase-witness/artifacts/before.wat`。今回試したAfterの状態規則はcheck.pyのencode/decodeと§4。共通更新のWasm Afterは不成立のため生成していない。以前のcapture.wat/capture.diff/capture.O2.watは計測用であり難読化Afterではない。実際のメッセージと通常・符号化状態をcases.json、Wasm観測をverification.jsonに保存。

## 12. 保存・再現

リポジトリルートから未作成出力先を指定する。保存済みの観測Wasmが必要。

```powershell
.\.tools\runtime-analysis-py312\Scripts\python.exe experiments/sha-zero-phase-gate/check.py experiments/sha-zero-phase-gate/reproduction
& 'C:\Program Files\nodejs\node.exe' experiments/sha-zero-phase-gate/verify.cjs experiments/sha-zero-phase-gate/reproduction
```

出力は上書きしない。manifest.jsonにコード・依存物・入力・Python結果のハッシュを固定。実行予算60秒、入力2件固定、メモリ上限は強制していない。CSEC原稿・コーパスを変更していない。

## 13. 限界

任意の別E_iや入力にも依存する表現を排除していない。今回の構成は既知の境界符号化の具体的な失敗例であり、新規難読化方式の成果ではない。完了条件の独立した原理・変換器・攻撃に対する優位性は未達であり、GoalをComplete又はBlockedにしない。
