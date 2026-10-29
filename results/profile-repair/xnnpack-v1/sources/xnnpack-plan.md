# XNNPACKの既存設計を使った反証試験

2026-10-24、実行前計画。固定commit `c754a15b2bed01e80679793cbe75ebc61312430f`のx8-lut kernel、hardware-config、x8-lut-configを読む。PSHUFB相当を検出して対応kernelを選ぶ構成は既存である。これを提案の発明として数えない。

1. u16の16-byte本体とprofile probeを最小WATへ転記する。元C全体のコンパイルやXNNPACK全体の実行ではない。実際のx86分岐はu32を選ぶので、u16本体への縮小とscalar fallbackの置換を明記する。tail、is_x86判定、init-onceは対象外。
2. 全256 byte indexと一般の256-byte tableに対するlaneモデルで、既存のprobeとkernelの組が両profileでlookupを返すか確認する。1個の共通Rをsite別Rへ弱めた場合と比較する。
3. 元・全strict・probeのみstrict・各kernel siteのみstrict・kernel全部のみstrictを実Wasmで実行する。壊れる変更は負例でありlibraryの脆弱性とは呼ばない。
4. 既存のdispatch自体が十分なら「修復不要」と判断する。性能を測るとしても既存kernelを維持した効果と扱い、新しいlookup algorithmや全面的速度改善としない。

固定入力は全byte indexを含むblockとseed乱数、tableはzero、identity、逆順、全one、単一bit基底及びseed乱数。Wasm memoryは1page、table[0,256)、input[256,272)、output[512,528)。全メモリを比較し、output以外の変更を許可しない。別profileは命令をstrict又はindex&0x8fを用いるstrictへ置いた実binaryで実行する。
