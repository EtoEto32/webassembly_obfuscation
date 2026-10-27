# 実験の修正履歴

2026-10-22追加：analysis-v3のguard検査だけでは、元fail引数が分岐以外の値に使われる場合を排除できなかった。
正常copy列の末尾で`memory[0] ^= (fail == 123)`を実行する有効Wasmは、検査した代表値0..Kでは一致し旧checkerに受理される。
auditに旧版の受理と入力123での不一致を保存した。元引数の使用を検査済みguardへ限定し、local0の上書き後の再利用は許す検査を追加。
最終analysis-v4で全60条件を再評価し48回復/12誤変換拒否、追加4拒否対照も通過した。
主変換器・main-v2・runtime-v2のbinaryは変更していない。

2026-10-21。

- 回復器の最初のO3 smokeでは、loadをlocalへ持ち上げたnative copyを読めずunsupported。
  成功経路のload由来を追い、抽出した操作は全失敗prefixのbit単位線形意味検査で確認するよう修正。
- analysis-v1はO3のdrop命令に未対応で中断。dropの子式を実行して値だけ捨てる規則を追加。
  どちらも解析耐性や主結果の失敗件数に加算しない。
- main-v1/runtime-v1のrotate32は2番目のcopy長が28で、退避領域も含んでいた。
  値・trapの検証には通る有効なcopy列だが、意図した「main 28byteを4byte回転」では3番目が冗長だった。
  長さを24に直しmain-v2、analysis-v3、runtime-v2を主結果として再実行する。
  v1の測定は履歴として保持し、v2の独立した追加サンプルに数えない。
