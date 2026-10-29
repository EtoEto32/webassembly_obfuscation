"""Remove stale scope statements while preserving unfinished requirements."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex';s=p.read_text(encoding='utf-8')
s=s.replace('この違いから，本稿で命令列まで確認した仕組みと変化量の比較は，主にCryptic Bytesに基づく．Proof-of-Theftでは設定と機構を照合し，2つの配布実装で出力と速度を実測した．', 'Cryptic Bytesでは設定横断の静的な変化と代表機構を，Proof-of-Theftでは配布設定と機構を照合した2つの実装の出力・速度を扱う．SWAMPEDでは入力標本の完全なハッシュ計算を確認し，公開変換コードによるnop挿入・整数定数分割の自生成対で機構，出力，速度を対応付けた．これらの実装間の独立性は未確定であり，データセット名の違いを独立した再現と数えない．',1)
s=s.replace('RQ2の10本は，互いに関連するCryptoNightの派生プログラムであり，他の採掘アルゴリズムでも同じ結果になるとは限らない．', '静的比較の元となるCryptic Bytesの10本は，互いに関連するCryptoNightの派生プログラムである．追加のローカル実測13バイナリもcn/0またはcn-picoに限られ，データセットをまたいで別の実装系統が含まれることは未確定である．他の採掘アルゴリズムでも同じ結果になるとは限らない．',1)
p.write_text(s,encoding='utf-8')
p=ROOT/'experiments/runtime-reference/csec-submission-draft.txt';s=p.read_text(encoding='utf-8')
s=s.replace('今後はビルド条件をそろえた対照と他の公開標本への比較拡張を行う．', 'SWAMPEDの入力標本にも公表出力を照合し，同じ組立条件でnop挿入と整数定数分割を生成して比較した．命令数は増えたが速度の反復範囲は重なり，小差を確定的な効果としない．今後は元配布の変換版を再現するビルドと，実装系統を確認した追加比較を進める．',1)
s=s.replace('Controlled builds and additional public samples remain planned extensions.', 'We also validate a SWAMPED input and compare locally generated NOP insertion and integer constant splitting under the same assembly conditions. Instruction counts increase, while the throughput ranges overlap across three repetitions. Historical rebuilds of distributed variants and comparisons with verified implementation ancestry remain unfinished.',1)
s=s.replace('同一条件の難読化版との比較は未完了．', 'この単独測定は実時刻を用いた旧条件である．後述の自生成対の測定は初期化時刻を固定した別条件なので，27.78 H/sと32.39 H/sの差を難読化の効果として比較しない．',1)
s=s.replace('確認済みの成果：10標本で適用可能な公表CN/0ベクトルに一致．', '確認済みの成果：Proof-of-Theft配布10標本とSWAMPED入力1・自生成2の計13標本で適用可能な公表CN/0ベクトルに一致．',1)
p.write_text(s,encoding='utf-8')
p=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/resume-state.txt'
with p.open('a',encoding='utf-8') as f:
 f.write('\n数値・主張点検：audit_runtime_report_numbers.pyで既存39blocks（wmp15/xmr15/SWAMPED9）のcount/elapsedからhashes/sを再計算し，3反復とSHA・最終出力条件，summary中央値/min/maxを照合して一致。runtime-number-audit.json保存。新しい計算は実行していない。原稿の静的10本とローカル13標本の範囲を区別しSWAMPED成果を考察へ統合。申込draftの未完了比較という古い文を更新し，旧seed27.78と固定時刻対32.39は別条件と明記。全系譜・元配布統一ビルド・全変換範囲・PDF6--8pageは未完了。\n')
print('Updated paper scope and submission draft to the verified current results.')
