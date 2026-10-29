# -*- coding: utf-8 -*-
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
marker='## コピーの観測引戻しの初期ゲート（2026-10-23）'
updates={
 'research/literature-review.md':'[range-pullbackの照合](range-pullback/prior-art.md)を追加。Kamath/PeterのISCA2024 (MC)²はlazy memory copyとsourceへのread転送を扱う直接近い先行機構。公式Wasm仕様の零長・範囲検査順を確認した。BAR2026のLLM/CTF分析論文も要旨と設計冒頭まで確認したが、未読結果を実測扱いにしない。',
 'research/research-gap.md':'値の座標変換から離れ、copy履歴を最終観測へ引き戻す案を[実装・反証](range-pullback/README.md)した。途中の更新を実体化しなくても、読み出し位置の局所条件式が元の更新列を露出させる。次案では、コードが長くなることやmemory命令が消えることより、公開された作用対応式からの回復を先に検査する。',
 'research/candidates.md':'[観測位置への引戻し](range-pullback/README.md)は、値の可逆符号化とは別の機構だが、lazy copy/read forwardingという既知原理に近い。意味保存と実装可能性は限定Wasmで確認。疎なreadでは高速だったが、12/12条件が元とbyte一致するコードへ戻った。最大のReject理由は既知最適化との近さと保護効果の欠如。一般変換器へ広げる前の初期ゲートで不採用とし、新規な発明数へ加算しない。',
 'research/threat-model.md':'range-pullbackの解析者には配布binaryと方式を与えるが、元parameter配置・source・seedは渡さない。privateなscratchは各callでresetし、値とtrapを観測対象にする。共有memory・export memory・途中のhost観測・persistent stateは対象外。元のcopy列への回復を解析タスクとし、時間差やtrapメッセージの文字列は意味同値性の契約に含めない。',
 'research/algorithm.md':'[引戻しの規則](range-pullback/algorithm.md)。各copy(d,s,l)に対して観測qを範囲内ならs+q-dへ戻し、全copyを逆順に適用する。ただし全copyのunsigned拡張された範囲検査と元queryの範囲検査を保持する。逆向きの条件式からd/s/lを抽出すればnative copy列へ戻せる。Wasmのimplicit stack operandとlocal.teeを順序通り扱う回復器を実装した。',
 'research/novelty-analysis.md':'[range-pullback](range-pullback/prior-art.md)は既知の遅延コピー・read forwardingとの技術差が弱く、Wasmのtrap保持自体を新発明にしない。途中memoryの消去と、この負荷での高速化は確認したが、全12条件を元とbyte一致するWasmへ戻せた。新規性・特許性・保護優位の確立とは扱わない。',
 'research/experiments.md':'[range-pullbackの実測](../results/invention-20261023/range-pullback-report-v1/report.md)。主36本92,544呼出し、11,760期待trapで不一致0。小モデル1,115,334 origin比較、別WABT144呼出しも一致。誤変換12本全てで反例。回復12/12は元rawとbyte一致。性能27process/189batchでは疎な1byte読出しに限定した最適化効果を測った。初回の短い計測batchは採用せずruntime-v2を確定値にした。',
 'research/novelty-status-20261023.md':'[copyの観測引戻し](range-pullback/README.md)も初期ゲートで不採用。36本92,544呼出しで値/trapは一致し、この限定負荷では高速だったが、公開された条件式から全12変換を元とbyte一致するWasmへ戻せた。lazy copy/read forwardingの先行性もあり、主特許候補は未確立のまま。',
 'paper-draft.md':'**Proposed Method / Implementation.** copyによる更新を実体化せず、最後のloadの位置を逆順のcopy範囲写像で初期memoryへ戻す限定Wasm変換を作成した。native copyの零長・範囲外trapを保存するため、unsigned i64での全範囲検査を保持する。\n\n**Evaluation.** 主36本92,544呼出し、11,760期待trapで不一致0。小モデル1,115,334比較、別WABT144呼出しも一致。全12変換条件は元rawとbyte一致するWasmへ回復した。疎な1byte観測の人工負荷では高速化したが、保護効果ではない。\n\n**Discussion / Conclusion.** lazy copy/read forwardingとの近さと、局所条件式からの容易な回復により主特許候補には不採用。任意Wasm・共有memory・実アプリへの一般化は未検証。[実装と再現](research/range-pullback/README.md)、[実測](results/invention-20261023/range-pullback-report-v1/report.md)。'
}
for rel,body in updates.items():
    path=ROOT/rel;text=path.read_text(encoding='utf-8')
    if marker not in text:path.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+body+'\n',encoding='utf-8')
path=ROOT/'research/novelty-status-20261023.md';text=path.read_text(encoding='utf-8').replace('18%使用（約82%残）','20%使用（約80%残）');path.write_text(text,encoding='utf-8')
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
line='2026-10-23追補：[copy履歴を観測位置へ引き戻す案](research/range-pullback/README.md)を初期検査。36本92,544呼出しの値/trapは一致したが、全12変換条件を元とbyte一致するWasmへ回復。疎なreadでの高速化は既知のlazy copy/read forwardingに近く、主特許候補には不採用。[実測](results/invention-20261023/range-pullback-report-v1/report.md)。'
if line not in text:path.write_text(text.replace('# webassembly_obfuscation\n','# webassembly_obfuscation\n\n'+line+'\n',1),encoding='utf-8')
path=ROOT/'research/notdec-baseline/README.md';text=path.read_text(encoding='utf-8');mark='## 2026-10-23のread-only再確認'
if mark not in text:path.write_text(text.rstrip()+'\n\n'+mark+'\n\nDocker infoはdockerDesktopLinuxEngineのpipe不在で終了。WSL一覧はsandbox内でE_ACCESSDENIEDだったが、承認されたsandbox外の同じ一覧取得ではdocker-desktopのみを返した。通常のLinux開発環境を得たことやNotDecの実行成功を意味しない。Docker/WSL設定変更、再インストール、factory resetはしていない。研究全体は別の仮説検査を継続している。\n',encoding='utf-8')
print('Integrated range-pullback; existing TeX edits were not touched.')
