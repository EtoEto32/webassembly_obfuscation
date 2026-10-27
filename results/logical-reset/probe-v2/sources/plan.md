# J：論理容量とセグメント寿命を分離するWasm再初期化

2026-10-24、実装・測定前の計画。既存のF-O/H/Iとは別に、リクエスト間の状態隔離を扱う。新規性は仮説であり、reset一般、snapshot、仮想容量、ソフトウェアbounds checkを発明したとは主張しない。

## 問題と近い先行技術

Wasmのmemory/tableは縮小できず、data.drop/elem.dropは元へ戻せない。値のコピーによるresetだけでは、新しいinstanceと同じ状態へ戻らない。Wasmtimeの[2026-09-10のreset提案 #14313](https://github.com/bytecodealliance/wasmtime/issues/14313)はこれらを明示しており、問題の発見と完全resetという目的は既知である。今回確認したFeature/Benefit/Implementation/Alternativesを根拠とする。公開issueであり査読研究ではなく、そこでの性能値は未追試。

Wasmtimeの[pooling allocator](https://docs.wasmtime.dev/api/wasmtime/struct.PoolingAllocationConfig.html)はメモリ再利用と初期化を実装し、[Wizer](https://github.com/bytecodealliance/wizer)は初期化状態を新しいmoduleへ書き出す。これらを弱い対照に置き換えない。まず同じcompiled Moduleからのfresh instanceを標準APIの対照にする。ランタイム内部reset・Linux poolingの直接比較は別の実装が必要で、今回のNode測定だけで優位としない。

## 差分仮説

実binaryを変換し、物理的に増加したmemory/tableと、guestが観測する論理容量を分離する。全ての該当操作を論理容量で検査し、セグメント破棄をprivate globalへ移す。初期化用のimmutable segmentを保持し、reset時に容量・drop状態・初期値を復元する。これにより標準Wasmエンジン上の同じinstanceで、guestから見える初期状態を再構成する。

候補請求の核は、容量・drop状態・全アクセスの仲介・初期像の再適用を対応させるbinary変換である。一般の仮想化とcheckpointの自然な組合せという反論を優先して検討する。

## 対象と観測

最初の実装は閉じたcore module、private memory32一つ、任意のprivate funcref table一つ、数値global、関数export、通常整数/浮動小数/制御構文、bulk操作。imports、start、shared memory、memory64、GC/EH/continuation、外部へ渡す参照やメモリは拒否する。初期状態はmoduleの宣言初期化直後。resetはtrusted hostがguest停止時だけ呼ぶ。これはWASI Componentの完全resetではない。

比較するのは数値結果・trapの有無・guestの論理memory/table状態・drop挙動。trapの表示文言、関数object identity、物理容量、実行時間、プロセスの残留byte、割当失敗時の同じ選択までは同一性を主張しない。成功可能なbounded allocationの下で比較し、memory.growの非決定的な失敗を明記する。

## 事前固定した検証

- 原本と変換を同じ操作列で比較し、reset後はfresh原本と再比較する。正常終了だけでなく副作用後のtrapも含む。
- memory/tableの成長、再成長、0長/OOB、重複copy、active/passive/declarative segment、drop後のinit、整数アドレスoverflow、値評価の副作用を含める。
- memory/globalのみ戻す不完全対照、論理boundsを省く対照、drop仮想化を省く対照の反例を確認する。
- raw/O3をNodeとWasmtimeで検査。最初の実装不備は別記録し、保護効果と数えない。
- fresh instance、提案reset、不完全resetの時間、binary size、変換時間、保持容量を測る。不完全resetは速度上限の参考で、安全な代替として扱わない。
- 再利用間の値・trap隔離を示しても、タイミング非干渉、全入力の証明、特許性の実証とはしない。

実装の成立後も、実需と先行構成との違いが不足する場合は主特許案へ昇格させない。
