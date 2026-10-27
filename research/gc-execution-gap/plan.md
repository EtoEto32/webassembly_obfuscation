# GC実行に至る障壁の測定（新方式と主張しない）

2026-10-27、実験前。直前の研究区切りはSの実装・比較・反証を保存したprogress。今回はR/Sの生成成功を実テストの価値へ直結できなかった原因を調べる。

事実: wasm-smith 0.262の `disallow_traps=true` は、struct.getやarray.get/set/fill/copyなどを生成対象から除外する。元のR実験ではfalseだった。trapを減らすという標準設定だけで、求めるGC命令の実行が増えるとは限らない。

仮説: 低いaccess数には、命令の不生成、未呼出しの関数、呼出された関数内での未到達、命令自身のtrapが混在する。入力値を深く構築するだけでは、それらの多くを解決できない。

実験: 無改変の公式wasm-smith 0.262へ同じ4型shape・64seedを与え、defaultとno-trapsを比較する。元Rと同じ定数式上限を使う。function-bodyのarray長は計測対象を安全な資源量に保つため既存と同じ31 maskを適用し、この変換が任意元プログラムの意味保存ではないことを明示する。bounded版へfunction-entry、GC命令直前/直後のcounterを追加する。null/深さ1の入力をfresh instanceへ与える。100,000fuelの同一上限を使い、counter追加がfuel消費を変える点を分離する。無計数版のstatus/resultも並べ、計数による差を隠さない。

評価単位はmodule単位とsite単位の両方。単に成功命令の繰返しが多いだけでcoverage増としない。trap/error/timeout/unsupportedを分ける。原因分類を新しいfuzzingアルゴリズムとは呼ばず、既存設定で解決しない必要性が確認できた場合だけ次候補の設計へ進む。
