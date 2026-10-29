# SIMD非正規マスク候補：事前仕様

2026-10-18。前回bit-feedbackは停止性のためのbit DAGが回復順序にもなるため不採用。今回は反復や依存の循環を使わず、SIMD比較結果の表現を変更する候補を検査する。採用済み・新規と断定しない。

対象はi8x16比較からBoolean演算を経てbitmaskを返す純粋な関数。真を255に固定せず正数、偽を0で表す。Q(x)=[x>0]とする。

```
E(a >_u b) = sub_sat_u(a,b)
E(a <_u b) = sub_sat_u(b,a)
E(a != b) = max_u(sub_sat_u(a,b), sub_sat_u(b,a))
E(a == b) = sub_sat_u(1,E(a != b))
E(A AND B) = min_u(E(A),E(B))
E(A OR B)  = max_u(E(A),E(B))
E(NOT A)   = sub_sat_u(1,E(A))
E(A XOR B) = min_u(max_u(E(A),E(B)),sub_sat_u(1,min_u(E(A),E(B))))
result = i8x16.bitmask(i8x16.gt_u(E(root),zero))
```

全命令のlaneごとの範囲は0..255。sat_subは通常のmodulo減算と区別する。帰納的にQ(E(P))=P。より広い整数幅、memory、例外、trap、副作用、分岐等への一般化は今回含めない。

先行するquantitative/robust logicのmin/max表現、Wasm SIMD仕様、既存vector obfuscationが近接する。技術的差分候補は、飽和差からBoolean cone全体を非正規値のまま評価する具体的な変換規則。新しい数学原理とは数えない。US8645930B2とWASMixerの間接呼出しは先に検討した方向であり、本候補の原理とは別に記録する。

保護目標は元の比較とBoolean結合の回復費用を増やすこと。方式とバイナリは解析者に公開し、元プログラム・変換レポートは回復に与えない。最も単純な攻撃としてQの交換則を使う抽象評価を先に実装する。値が255以外になったことやSIMD未対応は保護効果ではない。

比較：plain、各gate後に0/1へ正規化する対照、cone全体を融合した方式。3つの条件判定kernel、raw/O2/O3。境界・乱数・全byte入力組を照合。実行時間、size、process RSS、変換時間、解析時間を記録する。回復できるという理由だけで棄却せず、費用と先行技術との差を独立に判定する。単純な抽象評価で済むなら、seed・lane配置変更を次の発明に数えない。
