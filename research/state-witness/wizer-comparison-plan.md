# 既存Wizerとの直接対照

2026-10-25。公式Wasmtime CLI 50.0.0（2026-10-20配布）のWizerを実行する。Python binding 50.0.1というpackage版番号と混同しない。配布archiveのSHA256をGitHub releaseのdigestと照合した。

先行実装はdrop命令とtable更新を明示的に拒否し、active dataの寿命を空のpassive segmentとして保存し、元passive dataは保持する。この仕様をsourceだけでなく小さな独立対照で確認する。active/passive順序、起動済みmemory、0長memory.init、passiveからの後続copyを含む受理例を使い、未変換側はinitializerを実行し、Wizer出力側は既に初期化済みとして同じAPI列を走らせる。

data.dropが初期化にある、元APIの後続処理だけにある、到達不能関数だけにある場合とtable.initの例を別々に用意する。これらの拒否は「未対応」として数え、復元バグ・false positive・Kの性能優位には換算しない。Kは復元器ではなく診断器であり、製品間の勝敗表は作らない。

NodeとWasmtime Pythonで、受理例の返値/trap・公開memoryを比較する。有限実行が一致しても全入力の同値の証明にはしない。目的はKの主張に先行する機能と、残る対象の範囲を厳しく区別することである。
