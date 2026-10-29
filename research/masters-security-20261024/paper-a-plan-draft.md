# WIT効果計画による認可・実行の対応づけ：実装と適用限界

研究草稿、2026-10-24。新しい安全原理又は特許性を確立した論文ではない。生成器の有効範囲と、強い対照で残らなかった効果を報告する。[設計・請求項案](effect-plan-design.md)、[文献](prior-art.md)、[追加文献](prior-art-followup.md)を併読できる。

## Abstract

WebAssembly Componentの型から借用資源の位置を抽出しても、手書きの権限注釈と実行処理が食い違えば、その型検査だけでは実際の効果を保護できない。本研究では、限定した効果recipeから具体的なread/write計画を生成し、同じ計画から権限依存と実行を導くプロトタイプを実装した。実Componentの288条件が一致し、独立したrecipe解釈との576単体条件でも最終ファイル内容が一致した。一方、正しい手書き単一計画も同じ安全性を満たし、生成版の実I/O込み時間比は約0.994～1.018だった。結果は限定生成の実装可能性を支持するが、既知のcapability言語や計画実行を超える新規な安全性・性能優位を支持しない。

## Introduction

権限を持つresourceの型と、処理が必要とする権限は同じ情報ではない。例えばcopyのdestinationがborrow<file>であることから、writeを行うとは自動では分からない。認可抽出器とexecutorを別々に保守すると、一方だけを変更した場合に矛盾が起こり得る。初期方式の負例では誤注釈、対象の再読取り、非同期callbackによって明示した前提が破れた。

本稿は、認可と実行の対応を限定した命令定義へまとめる方法を調べる。WITを持つ既存アプリケーションへ無変更で適用できるとは仮定しない。研究の中心は、どの条件の下で対応が保てるかと、その生成に固有の利点があるかである。

## Related Work

SHILLとShillDBはcapabilityと実行時契約による資源操作の制約を先行して実現する。Omerの修士論文Wacky/ShimmerはWITからpolicy shimの雛形を生成する。ACEは計画の検証と、その計画に拘束された実行を組み合わせる。epoch失効や効果受付時の再検査も既知である。したがって、限定言語、固定計画、WIT adapter、失効検査のそれぞれを新規と主張しない。

本実装の具体的な対象は、borrowの有効期間中に実体を解決し、ホスト所有の計画と依存記録へ移し、呼出し終了後の受付で再検査する接続である。この接続が既知要素の自然な組合せ以上の技術的効果を持つかは未解決である。

## Motivation

第1方式は正しい効果契約と同期executorを信頼した。その条件下では安全でも、生成器が受理する契約を誤ってreadと指定したwrite処理を防げない。第2方式は独立のpermission属性を廃し、read/write opcode自体で権限を定める。また実行時に対象resourceを読み直さず、準備時の実体と値参照を固定する。

この設計の動機は確認済みの設定負例である。しかし、開発者が実際に犯す誤りの頻度や保守費用は測定しておらず、誤り率低減を実証したものではない。

## Threat Model

guestは型の範囲内で要求、alias、list長、option選択を変え、resourceのdropや後続要求を行える。hostのrecipe、opcode実装、resource resolver、権限台帳、FD owner、Jco/Nodeは信頼する。権限更新と受付は単一JS threadで同期的に直列化する。別thread・外部サービスの同時失効、host侵害、FD ownerによる番号再利用、非同期I/Oは保証の外である。

保護目標は、受付点で準備時から無効化された依存を含む計画を新規実行しないこと。既に実行した書込みの巻戻し、機密性の情報流方針、任意の事業ルールまでは保証しない。

## Proposed Method

入力は限定WITとread/write、list反復、option分岐を含むrecipeである。生成器はresource pathの型、read結果のスコープ、定数、命令数上限を確認する。

```text
prepare(args):
  ops = build_once(args)
  dependencies = permissions_of_opcodes(resolve_resources(ops))
  ticket = retain_and_record_generations(dependencies)
  ticket.plan = freeze_targets_and_value_references(ops)
  return ticket.id

admit(ticket):
  consume_once(ticket)
  serialize_with_revocation:
    if generations_still_valid(ticket):
      execute_only(ticket.plan)
  release_reservations()
```

readの結果は後続writeの値参照として保存し、文字列化を介さずbyteを渡す。aliasの権限は同じ実体へ集約する一方、使用したslot寿命は別に検査する。borrow wrapper自体を後続処理へ保存しない。

命令ごとの依存と実効果が規定通りなら、全命令の必要権限が受付で確認されることは命令列の長さに関する帰納で説明できる。ただし、これは信頼するopcodeに関する条件付きの説明であり、コンパイラ全体の形式証明ではない。

## Implementation

Pythonの限定WIT readerとJS builder生成器、Nodeのホスト台帳・同期file executorを使用する。実ComponentをJco 1.27.0でraw/最適化後に実行した。対象はread、write、copy、batch、optional、idleという自作APIである。標準WASIのoffset、stream、path、flags、一般result型を処理するadapterではない。

生成builderは3,298byte。入力schemaとComponent試験のschemaをhashで対応させる。生成器は独立permission属性、任意callback、scope外read参照等を拒否する。上限はlist4096、具体的操作8192、read/literal16 KiBであるが、Wasmからhostへのlift前の割当をこのbuilderだけでは制限しない。

## Evaluation

|評価|結果|解釈の範囲|
|---|---|---|
|実Component＋ローカルファイル|288条件一致、64拒否|固定したraw/optと6処理。全WIT対応ではない|
|不正recipe・executor|recipe6種類、外部callback2例を拒否|設定形式の制限。業務方針の正しさではない|
|独立したbyte oracle|12seed設定、異なるrecipe6種類、576入力一致|生成JS単体＋実ファイル。実Component576回ではない|
|単一計画の手書き対照|同じ36失効条件で両方式とも誤判定0|正しい手書きを超える安全性を確認せず|
|実I/O込み性能|20 fresh process、生成/手書き単一計画比0.994～1.018|小規模、warm OS cache、fsyncなし。高速化の証拠ではない|

性能は各方式5 process、30 warmup、9batch×50回。中央値とIQR、process memoryを原表に保存した。setup、prepare、継続、受付、同期I/O、releaseを含み、FD open/closeは含まない。旧版と新版の別測定の差を改善と解釈しない。

補助案としてlift前に費用を検査した。45条件は一致したが、共有descriptorをmemo化する方式は正しい非memo前検査に6例中5例で負けた。後検査に対する高速拒否は既存の上限検査でも説明でき、主発明には採用しない。

## Discussion

単一計画は独立した注釈とexecutorの矛盾を入力形式から取り除ける。しかし、同じ形式を正しく手書きする方式にも同じ利点がある。生成の価値を示すには、第三者adapterを同程度の表現力で置き換え、変更時の検査漏れや保守作業を比較する必要がある。

広い新規性の主張を、テスト件数や長い請求項で補うことはできない。本研究で得た成果は、限定実装、対応関係の前提、強い対照を置いた否定的結果、再現可能な試験である。

## Limitations

第三者アプリケーション未適用、型subset、単一thread、同期file I/O、小さい資源集合が主要な限界である。実行途中のI/O失敗は部分書込みを残す。resource由来のpolicyや内容依存の認可は自動導出しない。予算モデルは実割当量ではない。先行特許・文献の完全調査、特許性の法的判断、全入力同値性証明は未実施である。

## Conclusion

WITの借用資源から単一の固定計画へ認可と実行を結び付ける限定実装を作成し、正当性と費用を測定した。実装可能性は支持されたが、正しい手書き単一計画に対する明確な優位性と、強い特許新規性は未確立である。

## 再現資料

- [実Component試験](../../results/masters-security-20261024/effect-plan-v2/results.json)
- [生成器単体照合](../../results/masters-security-20261024/effect-compiler-audit-v1/audit.json)
- [強い対照を含む性能原表](../../results/masters-security-20261024/effect-performance-v2/report.md)
- [境界補助案の結果](abi-preflight-analysis.md)
- [全体の環境・実行手順](README.md)
