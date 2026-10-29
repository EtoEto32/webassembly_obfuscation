# SMTを使わない反例生成：成立範囲と実測

2026-10-24。[計画](guard-import-direct-plan.md)、[費用計画](guard-import-direct-cost-plan.md)、[長い列の追加計画](guard-import-direct-chain-plan.md)に対応する。新しい一般探索原理とは判定しない。

## 構成と限定した論証

二状態の一致条件を、cell値または定数の等式の連言Rとする。各importは観測対象のreadを先に行い、その後、対応する左右の実行へ同じ値と同じmaskを書き込む。API内部の写像はcopy/constantだけで、値による分岐・host再入・host例外・growはない。

任意部分書込みに対する普遍閉包は、この言語では `R ∧ close_all(R)` となる。no-opと全書込みは許される部分書込みなので必要性は直ちに従う。十分性はatomで示す。全書込みでも常に成り立つatomは、書込み対象を含まないatomか、同じcellの左右の一致など全書込みで恒真になるatomである。後者が書かれない場合の一致は元のRで保証される。異なる公開cell間や公開cellと固定値との等式は任意全書込みで保持されない。等式の連言に量化を分配して結論を得る。一般Boolean条件には成り立たず、[mask対照](guard-import-may-results.md)に反例がある。

全書込みで等式を破る入力は、全cellをbase値にした候補と、一つのcellだけ別値へ変えた候補の計N+1個から選べる。atomに代入後のhost変数がなければ、任意入力による不成立はbaseでも不成立である。同じhost変数同士なら不成立にならない。一変数と固定値の場合、異なる二代表値の少なくとも一方が固定値と違う。異なる二変数の場合は片方だけ変更すれば違う。このため連言が全候補で成立するなら全入力で成立する。memory代表は0/1、table代表はnull/一つの参照でよい。定数が他の値でも議論は変わらない。

[直接生成器](guard-import-direct.py)は失敗した固定点のrankを選び、各import直後に必要な条件を逆伝播する。readが既に違えば有効な残り入力を補う。そうでなければ、may-writeで現在の後続条件が偽ならno-op、必須writeまたは全書込みの不成立理由なら上記候補を選ぶ。API終了で観測差がなければ、一つ小さいrankで残った不成立をたどる。rankによる有限停止の議論であり、公式Wasm意味論に対する機械化証明ではない。最短性は主張しない。

このN+1候補は既に[API間書込み版](guard-environment.py)の`assignments`にも使っている。今回の差分はAPI内部の複数host境界とmay-writeへ接続した点であり、別の発明数には加えない。一般的な関係検証・effect/frame推論との比較は[文献表](prior-art.md)に記録した。

## 正当性の実行検査

|集合|条件・store|実行結果（各engine）|
|---|---|---|
|旧256＋may128契約|384契約、768初期storeの肯否が既存SMT版と一致|248否定caseを再生。560診断API、496準備call、436host call、256cell write、510pure tag call|
|別2-import対照|memory/tableの32否定store、一般SMT/BFSも否定|32反例、132診断API、64準備call。最長3 API|
|遅延chain|1/8/32/96 cell×read有無×must/mayの16契約|12生成反例、4肯定契約の一列対照。計1,128診断API、1,096host call。反例長2/9/33/97|

Node24.15.0とWasmtime50.0.1で再生した。最初の集合の肯定520初期storeは条件判定の照合であり、今回の直接生成試験で全列を実行した件数ではない。table値の観測には対照例の純粋tag関数を使い、任意関数の意味同値を検査したとはしない。最初の集合ではfresh referenceを既存のforeign tagへ単射で対応付け、その対応と実際の実行列を保存した。

ログ：[基本対照](../../results/state-witness/guard-import-direct-v1/manifest.json)、[2-import](../../results/state-witness/guard-import-direct-pair-v1/manifest.json)、[長い列](../../results/state-witness/guard-import-direct-chain-v2/manifest.json)。長い列のv1はharnessが正当なno-op入力を拒否したため中断し、[失敗記録](../../results/state-witness/guard-import-direct-chain-v1/failure.json)を保存した。修正後のv2だけを成功数に含める。

別の[記号検査](../../results/state-witness/guard-import-direct-lemma-v1/results.json)では、各sortの公開2cell/private1cellと三定数から作る90 atomについて、任意左右初期値・任意host値を使って候補の取りこぼしを探索し、全90件UNSAT・unknown0となった。これは有限atom配置の検査で、上記の任意Nの数学的議論を機械化したものではない。一般Boolean式 `x=0 OR y=0` は候補(0,0)/(1,0)/(0,1)で全て真、(1,1)で偽となるため、この候補基底を一般条件式に広げられない。

## 費用比較

[生データ](../../results/state-witness/guard-import-direct-cost-v1/results.json)。280否定caseを一batchとし、方式ごと3独立process、各2warmup＋5測定反復。Windows/Python3.9/Z3 engine4.13.3。case順はprocessごとの固定seedでshuffleした。

|方式|反例生成batch中央値|process中央値の範囲|共通前処理の中央値|
|---|---:|---:|---:|
|直接構成|22.457 ms|22.175–22.509 ms|2.662 s|
|自作SMT|848.841 ms|846.521–853.511 ms|2.650 s|

反例生成部分の比は37.80倍。前処理時間と各processの反例生成中央値を加えた概算は2.684 s対3.500 s、約1.30倍である。後者はend-to-endの反復測定ではなく、別計時値の和である。前処理はparseと共通固定点を含むため、38倍を解析全体の速度改善と表示しない。各反復で280反例・合計346 API・最大3 APIとなり、error/timeoutは0だった。長い列の追加試験はこの費用母集団に含まない。

whole-process peak working setは直接40,095,744–40,275,968 bytes、SMT67,526,656–67,710,976 bytes。比較harnessの両processともZ3をloadするため、直接CLI単独のmemoryではない。単独importでZ3をloadしないことは別processで確認した。

費用計画にはmask種類の記録も挙げたが、v1の各反復ログに保存したのは出力数とAPI数であり、mask別件数は未収録である。maskの実体は別の再生manifestに残る。この記録不足を埋めたことにはせず、mask比率による性能説明は行わない。速度は自作SMT対照との人工例での結果であり、先行著者toolや自然なアプリに対する優位ではない。

## 再現

repository rootで新しい出力先を指定する。

```powershell
python research/state-witness/guard-import-direct-test.py results/state-witness/direct-new
python research/state-witness/guard-import-may-witness.py results/state-witness/guard-import-may-pair-v2 results/state-witness/direct-pair-new --extractor direct
python research/state-witness/guard-import-direct-chain.py results/state-witness/guard-import-chain-v1 results/state-witness/direct-chain-new
python research/state-witness/guard-import-direct-lemma.py results/state-witness/direct-lemma-new
python research/state-witness/guard-import-direct-cost.py results/state-witness/direct-cost-new
```

最初の二つの既存control結果がない環境では、[再現packageの説明](import-artifact-readme.md)を使う。特化による費用削減は実測されたが、自然な用途不足と独立したアルゴリズム新規性の未確立という研究判断は変わらない。
