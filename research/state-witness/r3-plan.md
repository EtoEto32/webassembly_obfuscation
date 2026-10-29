# 実アプリ由来の閉じたbinaryでの適用可能性（実行前）

2026-10-24。公式の小例だけでは修士研究の実用的な貢献を評価できないため、Wasm-R3-Benchの公開済みstandalone replay binaryを調べる。record/replayを本研究の発明とはしない。

固定repository: `doehyunbaek/wasm-benchmarks` commit `576f499476060026f6c18cf6edd255ffcbeb5e4f`（2025-11-03）。27 binary、合計54,252,889 bytes。取得前に1 file 4 MiB以下・合計32 MiB以下・path辞書順というdownload上限を固定した。これにより大きな4本を除いた23本を対象にする。小さいbinaryへの選択バイアスを記録し、27本全体の結果に拡張しない。

まずWABT validationと既存K observer profileへの適用を検査し、状態形・imports/start・memory/table上限・segment modeを記録する。profileはこの段階で緩和しない。必要なら全結果を見た後に別の計画を作る。

受理moduleがあれば、READMEで指定されたentryを確認し、標準engineのresource budgetと実行timeoutを設けた元/変換後の差分実行を検討する。未受理を解析失敗や復元不具合に数えない。閉じたrecorded executionを検査しても元のwebアプリ全入力の正当性は示せない。

著者paper（OOPSLA 2024）のabstract、Introduction、§5.2、§6を読んだ。27/43 web appsからのreplay生成、SIMD/threads等の制限は著者の報告であって今回の再現値ではない。今回の目的はKと復元実装の追加対象を得ることであり、記録処理自体は実行しない。

## 静的監査後の追試計画

無変更のprofileでは2受理・21未対応だった。未対応の一部はimports/startではなく、WABTが`@custom "name"`として保持するname sectionが原因だった。guestのcore実行意味とは無関係なname sectionだけをbinaryのsection単位で除く前処理を別scriptとして追加する。元fileと他のsectionを保存し、出力を別directoryへ置く。debug名や`WebAssembly.Module.customSections()`の結果は同値要件から除く。K本体・分類器のprofileは変更しない。memory/tableの資源上限も維持する。この前処理後の受理数はまだ測っていない。

name前処理後は11受理・12資源上限未対応となった。受理集合のうちbullet/mandelbrot/pacalcは49/23/12 passive data segmentを持つが、元codeのdata.drop/elem.dropは0だった。このcorpusを寿命変更後の復元不具合の評価へそのまま使うことはできない。

続く実行は、受理11本の`_start`を、元/名前除去/observer付の3条件で比較する。V8のmax-memoryを256pagesに固定し、各moduleのchild process全体に45秒timeoutを設ける。各条件のAPI結果と全exported memory bytesを照合し、observerは実行前後で連続2回観測して非破壊性を検査する。private globals/tableの元binaryとの全状態同値はこの対照では主張しない。ウォームアップのない単発実行であり、性能優越の測定にはしない。資源上限によるtrap/timeoutを意味保存失敗と混ぜない。

Wasmtimeでは初回500,000,000 fuelで5正常終了・6 fuel枯渇となり、各3条件の状態と結果は一致した。未完走6本だけをfuelなしで再試行し、memory上限256pagesとchild全体45秒timeoutを維持する。初回の枯渇を消さず保存する。これにより完了までの差分比較を補うが、実行コスト比較の反復には数えない。
