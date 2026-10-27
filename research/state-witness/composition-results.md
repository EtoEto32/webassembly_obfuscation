# 関数参照observerと復元変換の合成結果

2026-10-24。[事前計画](composition-plan.md)。[確定実験](../../results/state-witness/composition-v4/results.json)は小さい自作module一つによる切り分けであり、一般的な変換合成の証明ではない。

## 三つの異なる結果

1. 元full observerとref.func getter版は、funcrefを返すsignatureがWeaveの対応範囲外なので変換で拒否された。Wasm自体のvalidationは通っている。復元不具合ではない。
2. funcref戻り値を使わずhostのTable.getで読む対照は変換・実行できた。しかしdirect function exportsはWeaveのwrapperを指すため、非nullの3slotが対応表に見つからなかった。元APIは17/29/17/trapを正しく返した。これはK側の対応規則の合成失敗である。
3. 元関数を追加private tableに並べるdirectory版は3slotを元index集合へ対応付けられた。同一関数の二つのslot、別関数、nullを区別できた。最初の4pollで各1回中断し別instanceへ復元した4条件も、完了後の全元memory bytes、table参照、drop後segmentのtrapが元と一致した。5番目はcheckpoint未到達。

directoryは既知の参照registryという手法であり、新発明とは数えない。関数一覧用のtableとactive segmentが増える。これらも対象変換を通るので、変換器から完全に独立した参照oracleではない。

[意図的な破損対照](../../results/state-witness/directory-control-v1/results.json)でもこの前提を検査した。元tableだけで二つの関数を交換すると差を検出したが、directoryも同じ交換で破損させるとdescriptorの差が0となり、元APIは17から29へ変わった。これは自作の相関破損でありWeaveに発見した欠陥ではない。directoryの信頼前提と元API対照の必要性を示す反例として保持する。

Weaveの`__weave_resume`はglobal/table shadowを再構成してから実行を再開する。したがってrestore直後のhost Table.getを元stateと比較する契約は採用しない。full observerは再開完了後に実行し、そのinstanceを以後再開しない。snapshotへのobserver wrapperの干渉問題も、directoryだけでは解消しない。

初回[composition-v1](../../results/state-witness/composition-v1/failure.json)はWindowsの標準文字encodingによるharness失敗。[v2](../../results/state-witness/composition-v2/results.json)では2方式の変換拒否を保存した後、console表示だけで同種のencodingエラーが起きた。v3以降はUTF-8でsubprocessを読み、consoleはASCII-safe JSONにした。これらをguest不具合件数に含めない。

```powershell
python research/state-witness/composition.py results/state-witness/local-composition
```

`prototype.py`の元profileと、固定したAPI分類器は変更していない。修正は別の合成用generatorに置いた。
