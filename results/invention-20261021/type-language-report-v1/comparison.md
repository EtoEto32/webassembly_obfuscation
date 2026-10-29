# 型回復の対照実験

O3、3 fresh Node processの中央値。各processは32768呼出しwarmup、16384呼出し×9 batch。
JS→Wasm呼出しとchecksumを含む。batch約0.6–1msの診断値で、小差の性能優位を確定しない。

| 入力族 | n | 形 | ns/call中央値 | process中央値の範囲 | bytes |
|---|---:|---|---:|---|---:|
| regular | 1 | loop | 37.775 | 36.792–38.196 | 113 |
| regular | 1 | peeled | 39.941 | 39.618–44.232 | 130 |
| regular | 4 | loop | 40.234 | 39.325–40.491 | 113 |
| regular | 4 | peeled | 41.547 | 38.934–44.019 | 217 |
| regular | 8 | loop | 46.558 | 43.097–48.761 | 113 |
| regular | 8 | peeled | 45.209 | 44.269–47.247 | 333 |
| forced | 1 | loop | 39.960 | 39.417–41.486 | 130 |
| forced | 1 | peeled | 39.825 | 37.408–41.479 | 113 |
| forced | 4 | loop | 44.336 | 44.250–45.972 | 130 |
| forced | 4 | peeled | 38.800 | 38.788–40.906 | 200 |
| forced | 8 | loop | 60.095 | 45.758–61.743 | 130 |
| forced | 8 | peeled | 44.855 | 42.529–46.423 | 316 |

全例linear memory 65536bytes。最大RSSはNode全processの値で、アルゴリズム単体ではない。
Retypdのfull solverは1条件1processの診断値。shape回復は1process内11反復の中央値で、測定法が異なる。
未実行・timeout・frontend未対応を回復失敗として加算しない。NotDec本体は今回未実行。
