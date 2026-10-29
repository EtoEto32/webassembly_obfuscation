# 制約の射影と128列の単位伝播

2026-10-21。これは検査した構成の説明であり、既知のCNF変換・resolution・単位伝播を新発明とする記述ではない。[先行資料](prior-art.md)を参照。

## 入出力と生成規則

入力は2–20個のv128入力を固定アドレスから読み、and/or/xor/notの非循環な計算を最大64gate実行し、最後のv128を固定出力先へ書く閉じたmodule。1page固定memoryとrun、arityだけをexportする。任意のC/Rust出力ではなく、正規化したmoduleが対応profileに一致する場合だけ受理する。

各gateに出力変数zを置き、例えばz=a AND bを次の三節へ変える。

```text
(¬a ∨ ¬b ∨ z) ∧ (a ∨ ¬z) ∧ (b ∨ ¬z)
```

出力をtrueに固定しない。全入力について、元DAGを評価した内部値と出力がCNFの一意な拡張を与える。

消去する内部変数xについて、xを含む節集合P、¬xを含む節集合Nを求める。PとNの全組からxを消したresolventを作り、tautologyと重複を除く。PとNを削除してresolventへ置き換える。入力変数と最終出力は消さない。

候補ごとに新しい節数・幅を調べ、幅8以下、節数が初期の1.5倍以下の候補だけを許す。候補列挙の費用を抑えるため、|P|*|N|が節数budgetの8倍を超える場合も見送る。許容候補のうちliteral数、節数、変数番号の順に最小を選ぶ。許容候補がなくなるまで反復する。全体最適化ではなくgreedyであり、これらの閾値に新規性を主張しない。

## 単位伝播をWasmにする

残る変数iごとに、trueと判明したbitのmask T_i、falseと判明したbitのmask F_iをv128 localへ置く。入力はT=input,F=not(input)、内部は両方0。正literal iのfalse maskはF_i、負literal ¬iのfalse maskはT_i。

```text
repeat:
  for clause C in a fixed shuffled order:
    for literal l in C:
      u = AND(false_mask(k) for k in C except l)
      if l is positive: T[l] |= u
      else:             F[abs(l)] |= u
  if T[output] | F[output] is all ones:
    reject a conflicting output mask
    store T[output]; return
  if pass bound exceeded: diagnostic trap
```

空のANDは全bitが1。更新は単調であり、同じliteralを再び導いても状態は変わらない。一つのv128で128個の独立したBoolean評価を同時に行う。laneをまたぐ算術やcarryは実装していない。

## 意味保存に必要な条件

1. gateの等価CNFは、入力を全て固定すれば、元DAGの依存順に単位伝播して出力を決められる。
2. 全resolventを含む変数消去は、残る変数についての存在射影を保存する。さらに、**初期割当が消去しない入力変数だけに与えられる場合**、残る変数への元の単位伝播を模擬できる。消した変数xを導いた理由節と、xを使って次のliteralを導く節をresolveすれば、xを経由しない理由節になる。この置換を単位導出の順に行える。消去後に存在しない変数へ新たな仮定を与える場合の保証ではない。
3. 元の正しい評価がCNFのモデルなので、伝播でそれと反するliteralは導けない。各bitでT_iとF_iの共通部分は常に0。
4. 固定点に達するまでの各未完了passでは、そのbitについて少なくとも一つの変数が新たに確定する。残存変数数Vに対してV+1 passの上限は十分。128列全てが出力を得てから書き込む。
5. 全load/storeは最初の336bytes以内で、1pageの固定memoryに収まる。入力を全て読んだ後に出力16bytesだけを書き、他のmemoryを変えない。import・並行実行・途中の外部観測がない。

この説明は対象profileの意味と既知の推論規則に基づく。parser・生成器・JITを含む機械検証済み証明ではない。有限実行テストの件数を全入力の証明へ読み替えない。資源不足、実行時間、debug位置は同値性に含めない。

## 同値性だけでは足りない反例

各節Cを `(C∨u) ∧ (C∨¬u)` に変えると、論理的には同じ条件になる。しかし、Cの未確定literalが一つになっても、uが未確定なら新しい二節はunitにならない。本実験では全節にこの変更を施した正しいWasmを作り、元のparity8の入力0で出力が伝播せず、raw/O3の両方で診断trapになることを確認した。メモリの変更はなかった。

従って、SATの充足可能性や論理的な同値性を保つ任意の前処理を採用できるわけではない。通常のSAT solverなら探索・resolutionを追加して解けても、今回の実行器は単位伝播のみで終了する必要がある。

## 方式既知の回復

公開ABIとbitごとの独立性を知る解析者は、128通りの入力を一度のrunへ詰められる。n入力の全真理値表はceil(2^n/128)回で得られる。これを既知のROBDDへまとめ、v128.bitselectを使う等価Wasmを生成する。元DAG、CNF、消去順、変換seedは与えない。

この攻撃は元のgate配置を取り戻すものではなく、同じ入出力を持つ別の計算を作る。bit間相互作用のある任意Wasmや、大きなnでの効率は保証しない。今回の生成範囲では、実行側のbitslicingと同じ構造が解析側の問い合わせも並列化する。
