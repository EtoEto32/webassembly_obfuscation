# lane選択のモデル修正と、120件を不具合発見に数えない理由

2026-10-26。`independent-v1`の不一致を追跡した記録。

## 観測

Node 24.15.0とWasmtime 50.0.1通常/決定設定の計1,536呼出しは、初期モデルで全てSATだった。SpiderMonkey 150.0.1の512呼出しを加えると、32/64ビットlane選択の120件でSMTと別の整数計算モデルが共に拒否した。120件は同じ傾向の入力・seed・O3有無の展開であり、120個の独立した不具合ではない。

`minimal-v1`では81byteの4本へ縮小した。aの各i32は255、bは0、maskの各i32は128とし、選択結果の下位i32を返す。32/64幅で、bitselectなら128、lane最上位bitなら0、byte最上位bitなら255になる。Nodeは0、SpiderMonkeyは255だった。SpiderMonkeyのbaseline/ion/baseline+ionで同じ動作だった。memoryやimportはない。

## 先行資料による反証

Core numericsの2026-10-23版・固定commit `aa4dcf44b8de3f3f3270ca067422172518ecc341` の読了箇所には、R_laneselectが0/1でbitselect又はlane最上位bitを選ぶ記述がある。一方、公式テストは16幅にbyte最上位bitを認める例を含む。さらに[issue125](https://github.com/WebAssembly/relaxed-simd/issues/125)では他の幅にもbyte選択を認める議論があり、[PR145](https://github.com/WebAssembly/relaxed-simd/pull/145)は2023-09-07にmergeされている。

従って、数式だけから作った二択モデルが実装の許容範囲を十分に表していると決めつけられない。現在の規範文書・生成文書・過去のmerge間の完全な整合は未解決である。議論の存在だけで、任意の出力を合法にしたわけでもない。参照interpreterの読了範囲ではlane選択をbitselectへ写しており、一つの許容動作を選ぶ実装を全許容集合のoracleにはできない。

## 修正後の扱い

`core-two`は初期の二択解釈を明示的に再現する診断modeとして保持する。新しいdefault `byte-compatible`は、bitselect、lane最上位bit、byte最上位bitを許す。異なるlane幅は別の選択変数とする保守的なモデルである。同じ幅の命令・同じrun内の選択は共通とする。これは規範仕様全体との同値性を証明したものではない。

この追加によって、SpiderMonkeyを含む2,048実行は独立した具体値checkerで全て説明でき、SpiderMonkey512実行は修正SMTモデルでもSATになった。v1の120件は**モデル差による診断**に分類し、脆弱性・新規engine bug・新規性の根拠に数えない。元のログを上書きせず、v2以降へ分離した。

16幅は依然として一般oracleの未対応に残す。minimal-v1での実行観測は残すが、未対応をモデル検証成功に数えない。

また、これは相関検査の独自の成功例でもない。二択解釈では一つの出力だけの所属検査でも255を拒否できる。同時観測を扱う新機構がなければ発見できなかった、という主張は成り立たない。
