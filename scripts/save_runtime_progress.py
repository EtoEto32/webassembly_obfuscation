"""Save traceable experiment coverage and outstanding requirements without completing the goal."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
P=BASE/'proof-of-theft'
audit=json.loads((P/'runtime-mechanism-audit.json').read_text())
checks=json.loads((P/'original-glue-public-vector-check-corrected-20261008.json').read_text())
by_sha={x['sha256']:x for x in checks['results']}
wmp=json.loads((P/'hash-throughput-preliminary-20261007-retry.json').read_text())
xmr=json.loads((P/'xmr-repeated-summary.json').read_text())
records=[]
for module in audit['modules']:
    if by_sha[module['sha256']]['status']!='all applicable public vectors matched':continue
    summary=next((x for x in xmr if x['sha256']==module['sha256']),None)
    report='proof-of-theft/xmr-repeated-throughput-20261008.json' if summary else 'proof-of-theft/hash-throughput-preliminary-20261007-retry.json'
    records.append(dict(sha256=module['sha256'],source=module['path'],dataset='Proof-of-Theft',
                       family=module['family'],build_flags=module['build_flags'],optimization_flags=module['optimization_flags'],
                       mechanism=module['mechanism_status'],label_build_conflict=module['label_build_conflict'],
                       correct_public_vectors=module['public_vectors_checked'],runtime_report=report,
                       seconds_per_block=30 if summary else 5,repetitions=3,
                       static_instructions=module['instructions'],static_bytes=module['bytes'],
                       causal_effect_established=False))
sw=json.loads((BASE/'swamped/046dc081-summary.json').read_text())
records.append(dict(sha256=sw['sha256'],dataset='SWAMPED',source='experimental_data/Cryptojackers_43/046dc081.wasm',
                    mechanism='not confirmed; public seed without a validated obfuscation pair',correct_public_vectors=5,
                    runtime_report='swamped/046dc081-repeated-throughput.json',seconds_per_block=30,repetitions=3,
                    causal_effect_established=False))
(BASE/'verified-execution-coverage.json').write_text(json.dumps(dict(scope='New completed runs only; prior Cryptic Bytes pool runs are additional reference evidence',
    modules=records,publicly_checked_and_repeated_modules=len(records),
    unresolved=['controlled matched builds','hash-core mechanism scope','SWAMPED obfuscation pair',
                'additional collected mining implementations','long-duration repetitions and browser comparability',
                'implementation genealogy','full paper consistency and 6-8-page rendered review']),indent=2)+'\n')
scope_path=BASE/'study-scope.json';scope=json.loads(scope_path.read_text())
scope['latest_verified_execution_coverage']='verified-execution-coverage.json'
scope['latest_goal_file']='C:/Users/ettotto/.codex/attachments/09b935de-1166-418f-a72b-2c8746fbe327/pasted-text-1.txt'
scope['completion_status']='incomplete; do not replace full objective with these preliminary completed runs'
scope_path.write_text(json.dumps(scope,indent=2)+'\n')
resume='''更新：2026-10-08 JST。前回ゴールターンは進捗あり。
最新ゴール：09b935de-1166-418f-a72b-2c8746fbe327/pasted-text-1.txt。添付main (3).pdfの対照と機構解析を新しいRQ2へ統合し、RQ1も刷新する。全目的は未完了。

実行状況：xmrのexec 13028、SWAMPEDのexec 47134、一覧再集計44252はいずれもexit0で完了。再開時に新しい外部状態を確認し、これらを進行中扱い・再起動しない。
完了実測：xmr-wasm 5標本×30秒以上×3反復、3秒ウォームアップ、原glue、1worker、ネットワーク無効。基準9.11 H/s、flatten6.18、split8.59、sub6.72、bcf23.08。全15ブロックの最終出力一致とnonce不変。公表CN/0の適用可能3入力を確認。bcfだけ-O2なので手法の効果としない。
webminerpoolhashcn 5標本×5秒×3反復は完了予備測定。同梱Makefileは基準含め全てbcfフラグなので4手法として扱わない。公表5入力にも一致。記録済み13pool出力への一致は別の補助証拠。
SWAMPED 046dc081…は新規にABI復元して公表CN/0入力5件全一致。30秒以上×3反復、中央値27.78 H/s、範囲26.54--28.13、全最終出力一致。元JS欠測、メモリとtime/getpidのhostを補った条件であり、難読化対の結果ではない。未対応hostはthrow。初回Docker呼出しはentrypoint未指定でChrome起動失敗、修正版は--entrypoint nodeで成功。遮断ファイルは迂回せず未取得を保持。

機構：xmr flatten hashラッパのstate offset8・pointer offset4・共通loopを確認。br_tableはない。xmr subラッパで(x-C)-6+C=x-6（C=1368051000）、n-(0-1)=n+1をmod2^32で確認。ただし両式は今回のCN0最大target測定で通らない経路。ハッシュ本体の機構範囲と因果説明は未完了。splitのラッパはstack配置の分割が見えるが制御フロー難読化と断定していない。
runtime-mechanism-audit.json、各WAT抜粋・差分、verified-execution-coverage.jsonで実測との対応を保存。
SWAMPED全42取得済みseedの完全なimports/exportsを照合。29seedは他取得コーパスと同一SHA、3seedはcore一致。独立実装と数えない。公開43のうち1つはI/O失敗で、原因解消・実行はしていない。seed-interfaces.json参照。

原稿：既存paper/main.texのみ改稿。xmr図表とSWAMPED実測、RQ1機構、条件の交絡、未計測経路を反映。申込案をcsec-submission-draft.txtに実際のタイトル・概要として再保存（以前はゴール文が入っていたため是正）。未送信。締切10月9日23:59 JST、本人が申込・投稿操作。
内蔵コンパイラはUnable to find standard directories for platformで引き続き失敗。コンパイル、PDF、ページ数、レイアウト未確認。別PDFは作っていない。
再現：proof-of-theft/REPRODUCTION.md。集計scripts/summarize_proof_xmr.py、summarize_proof_hash_experiment.py。機構auditを再生成すると追加subレビューが落ちるので、record_proof_substitution_mechanism.pyを後続実行する。
候補一覧のinstruction_count取得が先頭の関数内フィールドを読んでいた問題を修正し、inventory_cross_dataset_runtime.pyを再実行して最新CSVへ更新済み。主要速度表と全件static結果は完全JSONから取得しこの問題の影響を受けない。

次の必須作業：
1. ハッシュ本体のfunction対応と平坦化/置換/分割の機構を広げ、時間に含まれる変換範囲を確認。
2. 元source/compilerの条件を確定し、同じ最適化で通常版/変換版を再生成した対照を追加。AV遮断を迂回しない。
3. SWAMPED seedの同条件変換対を構成し、公開配布版と自生成版を明示して出力・反復速度を比較。
4. MinerRay/MineSweeper等の実サイト由来標本もsource/ABI/アルゴリズム根拠に基づき拡張。既存15k候補の全実行・全機構確認は未完了。
5. 元PDFの保存済み通常処理/計測対照を原稿の根拠へ統合し、新しい実装でも対照範囲を揃える。
6. 新規性比較表、紙面の構成整合、原稿6--8pageレビューを完成させる。現状はゴール完了としない。
利用枠は確認時19%使用、81%残。10%停止条件には未到達。
'''
(P/'resume-state.txt').write_text(resume,encoding='utf-8')
print('Saved 11 public-vector-checked repeated artifacts and full remaining scope')

if __name__=='__main__':pass
