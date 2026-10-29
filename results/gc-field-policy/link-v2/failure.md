# driverの集計不備

feature制限後の最初のNode条件はchecksum照合を通過したが、Pythonの`dict`生成に`engine`を重複指定して集計が停止した。実行ログはcommands.json。Wasmの不一致ではなくdriver errorであり性能結論には使わない。link-v3で重複指定を除去した。
