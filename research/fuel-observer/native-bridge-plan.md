# native fuel接続の検査（測定後に追加した計画）

2026-10-24。`native-fuel-probe-v1`の測定で、元raw例は論理費用+1、入口markerを追加したraw例は+4が観測された。O3後は異なる。この値を一般法則と仮定してはいけない。公開API docsも全命令が一律1とはしていない。Wasmtime50.0.1の該当compiler sourceは固定tag URLから取得できておらず、現時点では全入力に関する対応証明はない。

次の実験ではraw binaryだけに対し、内部fuelを外部の予約額と同じにする素朴版と、今回観測した追加費用4を付ける実験版を比較する。外部会計は既存guardと同じ公開履歴方式。公開イベントの後で予約額がdelta変わったら、内部残高にもdeltaを加える。予算不成立は既存guardと同じ公開境界で止める。内部fuel trapは別に集計する。

目標は、内部fuel trapが残る条件を検出すること。仮に補正版が全試験を通っても、一般native fuel対応済みとはせず、測定したsubset/engine版の接続試作とする。O3後の一般接続はこの4単位だけでは正当化しない。

参考: [Wasmtime Store API](https://docs.wasmtime.dev/api/wasmtime/struct.Store.html) fuel説明、[Slacked fuel metering #4109](https://github.com/bytecodealliance/wasmtime/issues/4109)本文。後者は2022年の提案であり、現在の内部実装が同じだと断定しない。fuelは機械時間そのものではない。
