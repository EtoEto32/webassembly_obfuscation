# 型signature区間を保持するWebAssembly検証スタックの予備評価

## Abstract

多値Wasmの検証では、小さいtype indexから長い型列の検査・展開が繰り返される。本研究ノートではintern済み型列の区間をoperand stackに保持する方式を実装し、配列方式・1件のsignature certificateを再利用する配列方式・wasmparserと比較した。40人工条件480processの測定ではwide signatureでstockより短時間だったが、単純なcached-flatでも効果の大半が得られた。さらに2つの型列を連結する反例では幅に比例する比較量が残った。新しい主研究成果の確立には至っていない。

## Introduction / Motivation

Wasmの構造化制御と多値型は、streaming validationを可能にする一方、1命令が参照する型の幅に検証費用が依存する。対象はuntrusted inputの検証資源である。既存の実行時fuel制御や難読化とは課題を分ける。

## Related Work

Wasm仕様、wasmparser・V8・WABTの実装、既存component validationの資源制限修正、Java bytecode verificationを調べた。[読んだ箇所と限界](prior-art.md)を別記した。hash-consing、型列共有、memoizationを新発明として扱わない。

## Threat Model

攻撃者はbinaryを選べて方式も知る。保護目標は受理言語を変えず、型列の反復処理を減らすこと。任意の検証入力に対する時間上限や、実行時のsandbox safetyを新たに証明するものではない。

## Proposed Method

immutable signature poolとchunk stackを使い、同じid・同じslice位置なら要素照合を省く。それ以外は通常のBottom-aware照合を行う。多値のpop/pushはchunkの除去・追加となる。[詳細と証明方針](algorithm.md)。

## Implementation

Rustで実際の.wasmを処理するCLIを実装。自作kernelはnumericの限定subsetに対応し、metadataを標準validatorへ委譲する。flat/cached/segmentでcontrol logicを共有し、比較を表現の違いへ近づけた。新規アルゴリズムの存在を前提にした実装ではなく、その必要性を反証する比較を含む。

## Evaluation

生成・境界362例の対応範囲は4参照検証器と一致した。公式522例中481 invalidも一致したが、正常moduleは15例とも範囲外だった。40条件480process、fragmented 3条件36processを測定した。最新stockに対する改善の多くはflat/cachedでも説明され、segmentが一貫して優れる結果ではない。公開保存データ217本の約489万signature箇所では幅64超がなく、一般アプリへの大きな効果は支持されない。[数値とばらつき](results.md)。

## Discussion

狭い実装差は確認できたが、「Wasm型列を共有して検査を省く」という説明だけでは一般的なcache最適化との差が弱い。幅512の交互callでcachedより約12%短かったことは、独立の研究貢献を単独では支えない。最悪ケース保護を主張する場合も、split signatureで幅依存が再発する。

## Limitations

対応言語が限定的、正常な公式大module未対応、人工例中心、single-machine、背景負荷未固定、測定器自体の前処理差、機械証明なし。no-mismatchは健全性証明ではない。新規性の検索も網羅性を保証しない。

## Conclusion / 修士主テーマの判定

**現段階では採用保留。改善実装・比較研究の一部には使えるが、新規アルゴリズムを主張する修士主テーマとしては弱い。** 最大のReject理由は「既知の型列共有／cacheで大半を説明でき、適用対象と一般保証が不足している」ことである。

昇格には次を満たす必要がある。

1. cached-flatやrange equality memoizationでは得られない、明確な問題・保証を定義する。単にcacheを増やして速くしただけでは足りない。
2. 対応範囲を実アプリへ広げ、通常ケースの退行とmemory増加を抑えたend-to-end比較を行う。
3. fragmented型列、異なるsignature間の比較、GC subtype等を含む最悪ケース費用を説明する。現在の限定的O(W+R)を一般保証にしない。
4. 標準validationとの対応を証明し、公式正常系・不正系を広く通す。

これはPに新規性が絶対にないという判定ではない。現有の証拠では、主テーマに必要な強さへ到達していないという判断である。Pの小改良を続けるより、異なる原理の候補を次に調べる。
