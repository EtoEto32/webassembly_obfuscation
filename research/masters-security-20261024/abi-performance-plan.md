# 展開前検査の性能比較

2026-10-24、測定前の計画。late/tree/memo各5 fresh process。固定seed2026102404で順序を混ぜ、warmup20、9batch×50呼出しのprocess内中央値とprocess間IQRを記録する。

tiny、共有中規模、共有超過、非共有超過、共有大規模超過、空leaf多重の6例。同じ64 KiB memoryを使う実Component。全呼出しにguest側descriptor構築・memory.fillを含む。比較は今回の抽象費用の同じbudget8192で行い、Wasmtime hostcall fuelとの速度比較とは呼ばない。Node RSSはruntime込み、GC後heapは参考値。memo前検査のMap自体にも費用があり、少数のdescriptorで優位とは仮定しない。

採否：正しいtree前検査を一貫して超えなければ、memo化は主発明要素に採用しない。後検査に対する改善だけでは、既存の前検査・fuel方式との差にならない。
