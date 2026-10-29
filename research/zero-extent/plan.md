# 零長を使う副作用の述語化：事前計画

2026-10-19。前回の書込み被覆とは異なり、条件付きの副作用をbulk-memory命令の長さへ移す。ただしif-conversion自体は既知であり、新発明と認定していない。EP1947584B1、MERIT (ECOOP 2026)、GCC PR102202の近接性を先に確認した。

## 検査する差

公開memoryの全byteが観測可能であり、memoryが0ページでもよい場合、非選択側storeをダミー領域へ向けるだけでは意味を保存できない。非選択側をアドレス0・長さ0のfill/copyへ変えれば追加領域なしで副作用を消せる。長さ0でも範囲検査は実行されるため、アドレスの選択も必要。

広幅storeは、同じ宛先へのidentity copyで全範囲を先に検査した後、各byteを長さ0/1のfillへ変える。非共有memoryではidentity copyは公開状態を変えず、失敗時にも部分書込みしない。即値offsetの非wrap加算はi64で計算する。prototypeはmemory maxを2ページ以下に限定し、i32に収まらない実効アドレスを確実な範囲外値へ写す。

仮説H1：全公開memory・trapを保つ零長述語化を実Wasmバイナリ変換として構成できる。
仮説H2：同じguardへ平坦化した通常分岐より、意味のある副作用条件の復元費用が増す。
H2は疑わしい。方式既知解析はlength != 0で条件を取り戻せ、byte fillやidentity copyを通常store/境界検査へ戻せると予想する。先にこの反証を実装する。

## 固定する評価

- 入力：1関数、1個の非共有memory32(min 0..2,max 2)、run/memory export、importなし。i32の全域的な純粋式、if/then/else、i32 store8/16/32、memory.fill/copy。sourceのlocal更新、load、call、loop、div、memory.growは拒否。
- 未変換、guard平坦化、identity-copy検査付きextent、明示的範囲検査付きextentの4方式、raw/O2/O3。最後の方式は機構アブレーションで新発明数に数えない。
- 0/1/2ページ、引数境界、offset overflow、random入力、trap後を含む全memory比較。誤った零長アドレス・事前検査省略・wrap offsetを負の対照にする。
- 解析器へ入力はバイナリのみ。元source/生成manifestを渡さず、bulk効果を条件付き更新と明示boundsへ正規化する。元のsource構文の一意回復を要求しない。
- 実行時間：10000 warmup、9×30000呼出し、3 fresh Node process。サイズ、変換時間、解析時間、RSS、公有memory量を併記。小例のJS呼出し費用を含む。
- 正常化成功率だけで不採用にしない。処理費用、実行負荷、既知変換との差を独立に判定する。特許性の法律判断は行わない。

これは先行性の疑わしい狭い技術差を試す反証ゲートであり、既存の独立3候補の代わりに数を水増ししない。
