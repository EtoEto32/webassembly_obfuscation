# 観測範囲とtrap後の利用契約の比較

2026-10-24。[計画](guard-protocol-plan.md)、[実装](guard-protocol.py)。選択する観測full/public/returnsに加え、trap後も呼ぶreenter、trapで列を終えるterminalを分ける。

## 実行と式の検査

[遅延観測13 module・39契約・78初期store](../../results/state-witness/guard-protocol-v1/results.json)では、reenterの57一致/21差から、terminalの65一致/13差へ変わった。消えた8差はpublic table6例とprivate byte readerのpublic/returns各1契約で、差を公開するためにtrap後の呼出しが必要だった。full契約はtrap時点の内部storeも比較するため13差が残った。

Nodeと[Wasmtime](../../results/state-witness/guard-protocol-cross-v1/results.json)各606 API呼出しで整合し、一致側の236テスト列は共通trapで終了した。肯定状態の有限実行は任意長列の証明ではない。別array式と独立した終端判定を用いた[39契約285再帰義務](../../results/state-witness/guard-protocol-check-v1/results.json)はUNSAT、unknownは0だった。

以前の134module/964storeでは両protocolの最終分類数は変わらなかった（full 571/393、public 634/330、returns 850/114）。この集合だけを評価してもprotocol差は分からず、新しい遅延公開の対照が必要だった。入力集合間で重複するmoduleを独立件数として足さない。

## より簡単な判定で十分な契約

現在の限定bulk profileでは、terminal/returnsだけなら初期状態で各APIのreturn/trapを一回ずつ比較すれば十分、という[命題と論証](guard-terminal-lemma.md)を得た。[専用判定器](guard-terminal-fast.py)は後続stateを列挙しない。初期storeが共通で、正常呼出しは同じstore更新と同じdrop集合を適用し、共通dropを増やしても各APIのreturn/trap一致が保存されるためである。

[147 module、許された寿命対7,536通り](../../results/state-witness/guard-terminal-evaluate-v1/results.json)で汎用固定点版と完全に一致し、5,482同一/2,054差となった。差の反例は全て長さ1だった。この全組合せ比較は解析器同士の比較であり、7,536組全てをWasm engineへ再実行したとは言わない。

同じ147moduleについて、任意寿命・任意の共通drop集合をBooleanで表し、別array実行式で正常時store一致・正常時寿命更新・共通drop後のoutcome一致を検査した。[963義務](../../results/state-witness/guard-terminal-check-v1/results.json)はUNSAT、unknownは0。共有parserからの限定modelについての確認で、命題全体の機械化証明ではない。

[適用外の反例](../../results/state-witness/guard-terminal-boundary-v1/results.json)はglobal phaseで分岐する。初期のprobeは両側trap、armは両側正常だが、arm→probeで片側trap/片側42となった。Node/Wasmtime各8 API呼出しで確認し、parserはglobals excludedとして拒否した。従って一回判定を任意Wasmに拡張できない。reenterを許す場合にも既存private-byte-readerが反例になる。

## 研究上の意味

「全ての契約で新しい固定点解析が必要」とは主張できない。限定terminal/returnsでは簡単な専用判定に縮退する。storeも観測する契約、又はtrap後に再入する契約と区別することに意味がある。interface automata、typestate、有限状態のprotocol制約は既知であり、今回の命題も限定profileの単調性に基づく簡約として扱う。新しい一般理論の成立とはしない。

```powershell
python research/state-witness/guard-protocol-cases.py results/state-witness/guard-witness-v1 results/state-witness/guard-contract-v1 results/state-witness/local-protocol
python research/state-witness/guard-protocol-cross.py results/state-witness/local-protocol results/state-witness/local-protocol-cross
python research/state-witness/guard-protocol-check.py results/state-witness/local-protocol results/state-witness/local-protocol-check
python research/state-witness/guard-terminal-evaluate.py results/state-witness/guard-witness-v1 results/state-witness/guard-contract-v1 results/state-witness/local-terminal-evaluate
python research/state-witness/guard-terminal-check.py results/state-witness/guard-witness-v1 results/state-witness/guard-contract-v1 results/state-witness/local-terminal-check
python research/state-witness/guard-terminal-boundary.py results/state-witness/local-terminal-boundary
```
