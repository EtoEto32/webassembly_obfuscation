"""Emphasize artifact-specific findings beyond general obfuscation descriptions."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper/main.tex';old=p.read_text(encoding='utf-8')
backup=ROOT/'paper/revisions/before-empirical-focus-20261008/main.tex'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():backup.write_text(old,encoding='utf-8')
replacements={
'難読化は，処理の内容を保ちながら':
'難読化手法と検出への影響は既存研究で説明・評価されている\\cite{harnes2024,cabrera2023,cao2023}．本稿で問うのは，公開された採掘標本で実際にどの処理が変換され，その処理を通る入力のハッシュ計算が正しいか，どのような性能変化が観測されるかである．設定名だけでは，適用範囲，通常処理との違い，実際の測定経路を確定できない．既存の手法説明を繰り返すのではなく，公開標本の根拠と出力・性能の結果を対応付けるため，次の二つを研究課題とする．',
'本稿では，公開資料からどの手法を確認でき':
'本稿の追加評価は，公開標本における変換の適用範囲と測定経路の対応，公表テストベクトルで出力を確認したハッシュ計算性能，静的な増加量と速度差の関係である．Proof-of-Theftでは配布設定の不一致を検出し，手法別の因果比較に使える範囲を限定した上で反復測定を行った．SWAMPEDでは空のimportを用いる既存評価と区別し，完全なハッシュ計算を復元した入力に公開変換コードを適用して同条件の対照を測定した．同じSHAの再収録や共通ソースの再利用も照合し，データセット名の数を独立した実装数と扱わない．新たな難読化アルゴリズムと検出回避能力は評価せず，未報告とする範囲は確認した先行資料に限定する．',
'本研究では，ファイルがどれだけ大きくなったかとともに':
'今回の結果では，静的な増加量と実行時の負荷をつなぐために，変換された処理と測定入力が通る経路を照合する必要があった．例えば，xmr-wasmの置換版は平坦化版より命令数が増えたが，速度低下の順序は逆であった．さらに，公開hashラッパで確認した置換式やvariant 4以上に限定された処理は，今回のv0入力では通らない．従って，ファイル全体の命令数と変換箇所の存在だけで実行負荷を説明すると，測定していない処理の効果を混ぜる．これは今回の公開標本と条件に基づく結果であり，平坦化と置換の一般的な優劣ではない．',
'同じ平坦化でも，LLVM系とTigressでは':
'SWAMPEDの自生成対では，nop挿入と整数定数分割による命令数比が1.097と1.034であるのに対し，速度中央値比は0.960と0.973であった．反復範囲が重なり，反復内の基準比は1の上下に変わるため，小さな速度差を確定的な難読化効果としない．一方，xmr-wasmの配布比較では歴史的なビルド条件を統制できず，特に偽制御フロー設定版の最適化条件が異なる．実際の変換対で条件をそろえる評価と，配布物の記述的比較を区別することが，測定結果を再利用する際の条件になる．静的なツール間分布の違いも，性能や検出回避の順位を単独では与えない．'
}
lines=old.splitlines()
for prefix,new in replacements.items():
    matches=[i for i,x in enumerate(lines) if x.startswith(prefix)]
    assert len(matches)==1,prefix
    lines[matches[0]]=new
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Introduction and discussion now lead with new artifact/path/output/performance findings; existing measurements preserved.')
