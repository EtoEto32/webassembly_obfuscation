# 有限環残差方式の実測比較

O3、5 fresh processの各9 batch中央値の中央値。範囲は5つのprocess中央値の最小–最大であり信頼区間ではない。時間は共通Wasm loopを含むhelper 1回当たり。

| 方式 | 時間 µs | process中央値の範囲 µs | binary bytes | 線形memory bytes | process最大RSS中央値 KiB |
|---|---:|---:|---:|---:|---:|
| original | 831.871875 | 826.375000–836.909375 | 29167 | 1114112 | 40876 |
| certified | 50.292578 | 49.448828–50.585156 | 29165 | 1114112 | 40884 |
| recovered-state | 0.256532 | 0.254265–0.256870 | 15445 | 1114112 | 39904 |
| recovered-io | 0.048159 | 0.047107–0.048403 | 2446 | 0 | 40068 |
| plain | 0.001023 | 0.001004–0.001033 | 69 | 0 | 39852 |

原型/129反復: 16.54倍。原型/全scratch再構築版: 3242.76倍。原型/I/O回復版: 17273.30倍。

plainとI/O回復版は全memoryの保存契約を持たない。scratch保存を含む比較はoriginal・certified・recovered-state間で行う。通常word式は解析器が発見した式ではなく、独立した下限側の対照。

RSSはNode全processの最高値であり方式単体の使用量ではない。binaryはbenchmark wrapper追加前、線形memoryは固定ページ宣言から算出。

main-v2のprepare_msは既に得た式の再コンパイルとO3処理を含む1回の時間であり、元DAGからの発明方式の変換時間や攻撃開発時間ではない。読取・回復本体の測定はreplay.jsonおよびrecovery.jsonに別記する。

plainはcalibration上限2^22に達したため10ms目標に届かず、各batchは約4.2ms。1ns程度の値はJIT内の共通loop・inliningを含み、単独JS呼出しの遅延ではない。
