# 共通profileを保つ部分決定化

## 問題と入力

同じoperator familyの環境parameter Rを、命令の出現ごとに別の自由変数としない。現行Wasm3のrelaxed swizzleではR_swizzleはプログラム実行中共通の0又は1である。これは仕様の既知条件である。

入力は実Wasm binary、保護するrun戻り値、各変更siteの正整数費用w_i。現在は2 i32→1 i32の単一run、直線式とi32 localのみ。relaxed swizzleはsplatされたbyte列をsplat indexで読みlane0を抽出する形に限る。全i32入力を扱い、byte化は下位8bitを取る。memory/import/global/float/loop/他relaxed命令を実装していない。

site iをstrictへ置くBooleanをh_iとする。変更後の戻り値をF(h,x,R)、全siteをstrictにした基準値をC(x)=F(1,x,0)と定義する。求める条件は∀x,R. F(h,x,R)=C(x)。変更前の各環境での値をそのまま保存する条件ではない。基準は元の合法profileであり、この純粋subsetでは得られた唯一の戻り値は元の合法な戻り値でもある。副作用や非決定性の残る別命令にはこの説明を拡張しない。

## 単調性がない例

data=全laneに255、index1=全laneに16、index2=全laneに32とする。二つのrelaxed swizzleからlane0を抽出してXORすると、R=0では0 xor 0、R=1では255 xor 255となり、どちらも0である。片方だけstrictにするとR=1で255を返す。両方strictにすれば再び0になる。

したがって有効なhが[0,0]と[1,1]でも、[1,0]は無効である。単に変更siteを追加する保守的更新という考え方は使えない。独立siteモデルは元の共通選択を過大近似するため安全側だが、この例でも2siteを変更する。ここでいう非単調性は当研究の模型・実Wasmで確認した性質であり、最初に発見したとの主張ではない。

## 反例駆動の選択

```
constraints = true
repeat:
    h* = argmin sum(w_i * h_i), subject to constraints
    SMTで ∃x,R. F(h*,x,R) != C(x) を問い合わせる
    UNSATなら h* を返す
    unknown / 時間・反復上限なら未解決として停止
    SATの反例x*,R*を取り出す
    constraints &= (F(h,x*,R*) == C(x*))
```

後半のhは記号のまま残す。制約は一般Boolean式で、等価関係や排他条件を保持する。既知のCEGISをこの意味モデルへ適用している。正のhitting-set節だけを収集する独自の新合成理論ではない。各反例は現在の候補を除き、完全な解を除かない。有限site集合で毎回厳密最小化し最終queryがUNSATなら、その費用は全ての有効集合の最小値である。実装は16site、query/optimizer各15秒、1024反復の上限を置くため、理論上の全候補探索完了を常に保証しない。

共通Rの代わりにsite別R_iを置く対照、戻り値の構文依存siteを全て変える対照、全siteを変える対照を実装した。費用は変更箇所の論理的重みで、実CPU時間ではない。重みの校正は未実施。

## binary変換と検証

WABTでvalidation・folded WAT化し、閉じた式集合を解析する。選定された`i8x16.relaxed_swizzle`だけを`i8x16.swizzle`に置換し、再度validationする。未変更siteは元の命令を保つ。出力hashだけでは信頼性を証明しない。

別のbyte-lane symbolic evaluatorは、最適化で導入されたv128 localとlocal.teeを扱い、再読したraw/O3 binaryの戻り値を基準と比較する。合成器のscalar transfer functionとsite番号を共用しないが、WABT・WAT parser・Z3は共通の信頼基盤である。

## 脅威モデル

正当なmoduleを配布するhostが、CPU/engineが選ぶ合法profileによって権限判断や検証値が変わることを避けたい場合を想定する。入力は全i32を含み、攻撃者に都合のよい値も含む。engineの仕様違反、JITの欠陥、host侵害、タイミング漏洩、実際の認証API、外部副作用は保護範囲外。元のポリシー自体が正しいことや、常に拒否側になることも保証しない。実験はローカル自作関数であり、製品の脆弱性検証ではない。
