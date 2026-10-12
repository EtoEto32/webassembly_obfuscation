"""Correct the earlier candidate-only overlap claim using all acquisition records."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
overlap=json.loads((BASE/'measured-corpus-overlap.json').read_text())
r=next(x for x in overlap['modules'] if x['name']=='046dc081-roundtrip')
assert r['exact_datasets']==['minerray','swamped','wasmbench','wasmixer','wasmmal']
seed=json.loads((BASE/'swamped/seed-interfaces.json').read_text())
assert seed['summary']['exact_overlap_seeds']==35
old='取得済みの他コーパスに同一SHAと同一core SHAの一致はなかったが，実装の系譜まで独立と確認したわけではない．'
new='取得記録全体でSHA-256を照合すると，この入力はMinerRay，WasmBench，WASMixer，WasmMalにも同じバイナリとして収録されていた．初期の採掘候補一覧だけを用いた照合ではこの重複を見落としていたため，全取得記録との照合へ改めた．同じ標本の再収録を独立した実装とは数えず，本稿の追加評価は完全な出力検証と自生成変換対の比較という対象・条件で位置付ける．'
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8');assert old in s;s=s.replace(old,new,1)
needle='各グループ内では，SHA-256が一致するファイルを一件にまとめた．'
addition='SWAMPEDの取得済み採掘入力42種類のうち35種類は，保存済みの他データセットの取得記録にも同一SHAで含まれた．'
s=s.replace(needle,needle+addition,1);p.write_text(s,encoding='utf-8')
# Prevent an earlier authoring helper from restoring the rejected statement.
p=ROOT/'scripts/integrate_swamped_hash_result.py'
if p.exists():
    s=p.read_text(encoding='utf-8');s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=ROOT/'experiments/runtime-reference/csec-submission-draft.txt'
with p.open('a',encoding='utf-8') as f:f.write('\n重複確認の訂正：SWAMPEDで実測した046dc081…入力はMinerRay・WasmBench・WASMixer・WasmMalにも同一SHAで含まれる。別データセットの独立標本として数えない。完全な出力検証と今回の変換対・測定条件を追加したことを貢献として説明し，同標本が世界で未評価だったとは主張しない。SWAMPED取得済み42seedのうち35seedは他取得データセットに同一SHAがある。詳細はmeasured-corpus-overlap.jsonと修正済みseed-interfaces.json。\n')
with (BASE/'proof-of-theft/resume-state.txt').open('a',encoding='utf-8') as f:
    f.write('\n重要訂正：audit_measured_corpus_overlap.pyで全取得109868records（coreはcandidate20783限定）照合。SWAMPED046dc081はminerray/wasmbench/wasmixer/wasmmalにも完全SHA一致。ローカルobjectを実際にSHA照合し一致。従来seed-interfacesの候補限定exact探索はこの標本を見落としていた。audit_swamped_hash_interfaces.pyを全取得exact比較へ修正し42seed再解析，35seed重複（旧29訂正）。core比較はcandidate限定3seedのままscope明示。原稿の「他corpus同一SHAなし」を撤回・修正，draftにも訂正。再収録を独立実装/新規標本と数えない。新規性は追加の検証・変換・条件比較として先行研究と照合する。新しいハッシュ計算なし。\n')
print('Corrected cross-corpus overlap claims and their generating helper.')
