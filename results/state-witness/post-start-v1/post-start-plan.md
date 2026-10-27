# 起動後のsegment寿命差に対する到達可能性検査

2026-10-24。ffmpeg.wasm core-mt 0.12.10の7,320個のinit/dropがstart関数へ集中するという観測を受けて固定した追加実験。結果を見て閾値を変更しない。

## 問いと判定

正常にinstantiationが完了し、実行中のframe・保留continuationがない二つの状態を考える。公開・非公開のstore、host、codeは同じで、data/element segmentの生存状態だけが違う。将来の通常のhost/Wasm API操作から、その差を観測できるか。

全export関数と、module中に現れる全てのliteral関数参照をrootとする。element segment内の関数、global/tableの初期化式、関数bodyのref.funcを含め、到達不能な場所やdeclarative segmentの参照も除外しない。direct call / return_callの閉包を取る。indirect/ref callでこのinstance内部の関数を得るには、その関数のexportまたはliteral参照が必要であるため、個別のpoints-to解析をせずrootに含める。外部moduleへのcallやhost reentryにも同じ制約を適用する。

この集合にsegment内容/長さを読む命令がなければ、segment寿命**だけ**の相違は観測不能と判定する。readerはmemory.init、table.init、およびGCのarray.new_data、array.init_data、array.new_elem、array.init_elem。data.drop/elem.dropは冪等な破棄でありreaderではない。len=0のinitもtrap条件を変え得るのでreaderに数える。readerが残る場合の出力は「不明」であり、不具合認定ではない。

## 適用の前提

- startは完了済みで、自動的に再実行されない。exportやliteral参照があれば通常のrootになる。
- 中断したstart、保存された内部frame、継続、debugger/engine-private経由の内部関数呼出しは対象外。
- 関数body・table/global等の状態は二状態で同じ。復元器が内部関数を追加exportした場合は、その**変換後module**を検査する必要がある。
- 誤った復元によるmemory/table/global/host差は判定しない。共有memoryへの外部書込みが同じでも、それ自体はsegmentを生かしたり内部関数参照を生成したりできない。
- wasmparser 0.227.1がvalidationできるcore moduleを対象とし、componentは拒否する。未対応命令を無視してparse完了にしない。

## 検証

全root種類、直接・間接・tail call、GCの4種reader、zero-length reader、dropのみ、到達不能readerを含む小さな独立controlを生成する。期待する静的判定を先に指定する。通常のMVP/bulk controlについて二engineで寿命差を作り、公開APIからの差の有無を測定する。静的に不明でも、観測不能なcontrolを置き、十分条件であることを確認する。

ffmpegの二標本を新scannerで再解析する。source/provenance/executable/source hashを保存し、旧scannerの結果を上書きしない。用途は適用可能性のふるい分けであり、既知のcall-graph reachabilityを新しい発明と呼ばない。
