# 公開履歴に応じた累積予約と返金

## モデル

元binaryの実行を、非負整数のopcode費用と公開event列で表す。費用は変換前の論理量であり、機械時間・engine固有fuelではない。初期予算と後続の予算入力は公開される。公開eventは`mark(id,payload)`と正常return。marker引数は現在のsubsetでは定数に限る。各分岐は静的には独立な非決定選択として扱う。実行可能性の過大近似であり、同じ述語を再検査した相関は失われる。

公開済みの履歴hと整合する構文経路の集合をP(h)、次のmarker又はreturnまでの累積費用をC(p,h)とする。

`U(h) = max { C(p,h) : p ∈ P(h) }`

入口でU(ε)を予約する。markerが起きたら、まず元のeventを公開し、その後でhを更新する。予約済みの累積額qをU(h)へ変更する。差が正なら残高から引き、負なら返金する。必要額が残高を超える場合は、その公開prefixの直後で停止する。returnも公開してから、完了する経路だけの累積最大費用へ精算する。

```text
analyze original module into conservative finite weighted traces
group traces by published event prefixes; compute U for each prefix
bind instrumented module bytes to the trusted generated contract

q := 0; h := empty
adjust(U(h))                # before original code runs
on original marker e:
    publish(e)              # do not use e to charge before publication
    h := h + e
    accept any public budget input for h
    adjust(U(h))
on successful return v:
    publish(return(v))
    adjust(max total cost among terminating traces consistent with h)

adjust(target):
    delta := target - q
    if delta > public balance: stop
    balance := balance - delta
    q := target
```

## 支払済み費用を返しすぎない条件

各marker到達前は、前の予約がそのmarkerまでの全候補経路費用を覆う。公開後のP(h)は実経路を含み、各候補の次の境界の累積費用はその候補の過去費用以上である。従ってU(h)を下げても、実際に既に実行した累積費用を下回らない。非負費用、非trap、有限経路、正しい保守解析が必要である。

これが「実費との差をそのまま返す」こととの違いである。実費は未公開の分岐を含み、同じ公開履歴でも異なり得る。返金先は実費ではなく公開履歴で決まる上界である。

## 公開時点を守る条件

次の課金・返金・予算停止は、公開済み履歴と公開予算入力の決定的関数である。同じ履歴と予算を持つ実行は次の会計判断も同じになる。実行中の秘密状態や将来の出力を使わないため、会計は未公開情報を先に開示しない。event又はreturn自体が許容する情報公開は外部契約で指定する。実時間の差まで消すものではない。

## 同じ公開語を持つ経路の集約（第二版）

同じ構文継続位置で、公開event列が等しい経路をまとめ、累積費用と各event到達費用をそれぞれmaxで保持する。後続の費用加算はmaxと分配し、分岐合併もmaxであるため、今回の独立分岐近似が算出する各U(h)を保てる。全費用vectorを同時に達成する実経路の存在は要求しない。公開語が異なる経路は混ぜない。

この集約は一般のmax-plus計算・動的計画法の応用であり、新しい代数と主張しない。最大4096行、event数32、構文深さ32の上限があり、公開語自体が指数的に増える場合は拒否する。少数の公開語に多数の隠れた構文経路が対応する場合だけ、列挙を減らせる。

## 最適性の限定

与えた保守的経路集合、marker間に課金点を置かない規則、借金を認めない会計のもとでは、次の境界までの最大費用U(h)より低い予約は集合内のある経路を覆えない。これはその抽象モデルの点ごとの下限である。実経路集合の正確な最適値、CPU時間の最適値、全手法に対する最適性ではない。`correlated`では実最大94に対し158を予約する反例を残した。

以上は紙上の帰納的論証であり、Lean/Coq等での機械証明ではない。
