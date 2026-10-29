# 論文草稿追補：Component Model resource破棄への計算移動

## Abstract

WebAssembly Component Modelの所有resourceとdestructorを利用し、計算payloadの準備順と状態更新の実行順を分ける変換を実装した。実coreバイナリからcomponentを生成し、JcoによるJS+core実行、通常最適化、公開結線の記号解析を比較した。主・追加104条件で459,680呼出しがoracleと一致した。生成順変更による追加解析費用は確認できず、独立した主発明としては採用しない。

## Introduction

目的は正当なソフトウェアの知的財産保護であり、解析不能性や暗号化ではない。言語固有の所有権・破棄意味を利用すれば、直接の算術命令から計算の実行点を移せる。しかし型・実体・canonical操作の公開結線は解析者にも利用できる。

## Related Work

Component Modelのresource機構は既定の仕様である。Wobfuscatorは言語境界への計算移動、ABI Debiasingは実行形式が与える解析手掛かりに関する近い背景を持つ。US20080289045A1には変数を破棄するdestructor atomがあり、語だけで今回と同一と判断しない。[読んだ資料・範囲・相違](prior-art.md)を記録した。

## Motivation

全payloadを準備してから異なる順で破棄すると、通常の関数単位の解析ではpayloadと作用点が離れる。この対応づけが実行負荷に見合う解析費用を作るかを検査する。

## Threat Model

解析者は全component、標準仕様、変換方式を知る。原本・seed・manifestは与えない。保護課題は同じ32bit関数を持つcoreプログラムの回復で、特定検出器の回避は課題にしない。解析器の未対応と誤答を区別する。

## Proposed Method

入力はxを初期状態とする1..128段の純粋なi32更新鎖。payloadはyだけから計算する。内部bufferにpayloadを保存し、byte位置をresource表現として生成する。各演算のresource型は対応する状態更新helperをdestructorに持つ。全生成後に元の演算順で明示的にdropする。[疑似コードと意味保存条件](algorithm.md)に示す。

## Implementation

Python変換器、WABT 1.0.42、Jco 1.27.0、内部最適化Binaryen 130.0.0、Node 24.15.0を使用した。Jco生成コードで任意repのbit30が失われる反例を確認したため、値ではなく小さい位置番号を渡す構成へ修正した。bufferを使用する直接helper版を比較対象とし、bufferの有無とresourceの効果を区別する。

## Evaluation

主72条件318,240呼出し、追加32条件141,440呼出しで不一致・trapは0。意図的な破棄順誤り9例はすべて検出した。主の元/回復coreへの別実行器567照合も成功した。104条件すべてから回復coreを生成した。

135 fresh processの実行測定と360回の解析から、O3後deferred/directは実行約0.989–1.413倍、解析本体約1.097–1.293倍。deferred/immediateは実行約0.949–1.047倍、解析本体約0.950–1.086倍だった。順序分離そのものによる優位性は確認できない。plain componentも元coreの約95.5–497倍を要し、Jcoの呼出し処理が小kernelでは重い。[実測・測定手順](analysis.md)に絶対値、サイズ、memory、分散を示す。

## Discussion

newを記号handle、dropを型定義のdestructor呼出しと解釈すると、生成と破棄の対応は辞書で求まる。bufferの位置も公開定数で、入力を列挙する必要はない。通常最適化後に構造が残っても、この意味解釈に対する耐性を意味しない。解析本体の有限な費用増は報告するが、人間の解析費用への倍率は主張しない。

## Limitations

対象は合成されたpure整数鎖13例。一般CFG、外部副作用、借用、再入、資源不足、別native component runtimeを扱っていない。出力はcomponent形式であり、coreと同じローダで置換できない。入出力の対応は32bitパターンによる。有限実験と紙上の条件付き説明は全入力の機械証明ではない。特許性、既存難読化器全体に対する優越性は未確立である。

## Conclusion

resource破棄で計算を実行する構成を実バイナリへ実装し、その公開結線を使う回復も実証した。生成順を変える部分の追加保護効果が弱く、本方式を主特許候補には採用しない。実行形式への移動を新規性・解析耐性と取り違えないための反証として保存する。
