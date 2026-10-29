# ページ内ブロック表現と書込み前の読込み：事前計画

2026-10-21。前区間は保存された有限環方式の評価を再確認しただけで、新方式の開発については no progress。ここでは別原理の、Wasm のメモリ表現変換を実装する。既存有限環方式の構成的提案は維持する。

## 仮説

元の private memory32 を、同じページ数の private memory64 に置き換える。
16 byte ごとの零保存の可逆写像 E で全メモリを表す。元アドレス p と即値 offset は、unsigned i32 を i64 に拡張してから加える。元の整数アドレス式の i32 wrap はそのまま保持する。

元の幅 w=1,2,4,8 のアクセスに対し b=floor(a/16)*16、e=floor((a+w-1)/16)*16 を求める。書込みは b と e の ciphertext block を先に読み、両方が読めてから復号・変更・再符号化する。Wasm のページ長が16の倍数なので、最後の block の全幅 load が成功する条件は元アクセスの範囲条件と一致する。必要な read-modify-write の load が範囲検査を兼ね、追加scratchページは不要。外部からアクセスできない非共有メモリ、実行中のhost呼出しなしが前提。

符号化やFeistel型の可逆更新そのものを発明とはしない。検討する差分は、Wasm のページ・有効アドレス・trap 後状態を使う具体的な lowering 規則。一般のload wideningとの重複、WASMixer/WeBMOとの比較が必要。優先権や特許性は未確立。

## 実装する比較

- plain：元 memory32。
- lifted：符号化なし、memory64へアドレスを拡張。
- byte：同じ符号化。最後のblockを先に検査し、byteごとに復号・更新。
- block：同じ符号化。接触する最大2 blockだけを復号・更新。
- bad-partial：事前読込みを省いた誤ったbyte更新。境界跨ぎで反例を要求。
- bad-wrap：即値offsetをi32加算にした誤変換。大offsetで反例を要求。

変換器は実wasmを読み、単一・固定ページ・非共有・非exportメモリ、i32/i64 scalar load/store、通常の関数/制御、定数active dataに制限する。import、start、table、global、bulk、memory.size/grow、元memory64、SIMDソース、custom情報の完全保存などは非対応。対応外は拒否する。

## 検査と採否

全8bit値、境界、符号拡張、非整列、byte境界/ページ境界、大即値、アドレス式と値式の副作用、trap前の書込み、trap後の次呼出しを検査する。全論理メモリを独立JS codecで復号して比較する。0/1/2ページ、raw/O3、別実行器の小範囲照合を予定する。

解析者は方式を知り、binaryもメモリも観測できる。逆codecによるメモリ回復を実装する。幅を変えたことや逆コンパイラ未対応を保護の成功にしない。正当性と実装費用改善があっても、それだけで新しい主難読化方式とは採用しない。

性能は同じ入力・状態・符号化で byte と block を比較し、plain/liftedを併記する。共通Wasm loop、warmup、複数fresh process、中央値と範囲、size、固定linear memory、process RSS、単発変換時間を保存する。実験後に成功条件を緩めない。
