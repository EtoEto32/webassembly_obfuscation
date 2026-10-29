from pathlib import Path
import hashlib
import json

repo = Path(r'C:\Users\ettotto\Documents\wasm-structured-encoding')
stage = Path(__file__).resolve().parent
changes = {}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def update(relative, transform):
    original = (repo / relative).read_bytes()
    text = original.decode('utf-8').replace('\r\n', '\n')
    updated = transform(text)
    assert updated != text, relative
    target = stage / 'updates' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated, encoding='utf-8', newline='\n')
    changes[relative] = {'before_sha256': digest(original), 'after_sha256': digest(target.read_bytes())}

def readme(text):
    text = text.replace('# Wasm Structured Encoding — 研究候補の試作', '# Wasm Structured Encoding — 既存符号化の適用試作')
    text = text.replace('2026年10月11日に調べた一次資料と、重複・未確認点を `docs/related-work.md` に記録しています。',
        '**2026-10-11の新規性監査：現状を新アルゴリズムとして採用しません。**\n'
        '2006年の多変数符号化と2007年の領域別符号化・境界変換合成に直接の先行例がありました。\n'
        '追加実験でも、対象42本の固定制御条件下の入出力式は各3回の問い合わせで再構成できました。\n'
        '根拠・適用条件・限界は [新規性監査](docs/novelty-audit.md) に記録しています。')
    text = text.replace('| `docs/design.md` |',
        '| `docs/novelty-audit.md` | 先行研究の該当節、棄却判断、42本の追加解析結果 |\n'
        '| `docs/novelty-search-log.md` | 検索語、確認範囲、アクセスできなかった資料 |\n'
        '| `tests/affine-recovery.cjs` | ソース・符号化情報を読まない入出力式の推定 |\n'
        '| `artifacts/affine-recovery.json` | 1,344条件の推定係数・検証結果・SHA-256 |\n'
        '| `docs/design.md` |')
    text = text.replace('新規性・解析耐性・検知回避・性能上の優位性は未確認です。',
        '新アルゴリズムとしての新規性は支持できません。今回の限定的な入出力解析への問い合わせ数の増加もありません。\n'
        '一般の解析耐性・実行性能の優位性は未評価です。過去のmanifestにある `novelty: unverified` は生成時の記録として保持しています。')
    return text

def design(text):
    return text.replace('## 研究候補',
        '> 2026-10-11監査：この案を新アルゴリズムとして採用しない。多変数符号化・領域別切替・境界合成に直接の先行例がある。\n'
        '> [新規性監査](novelty-audit.md) に出典と追加実験を記録した。以下は試作の設計記録として残す。\n\n## 研究候補', 1
    ).replace('新規性は未確定。通常のコード保護・解析研究用で、マルウェアの検知回避を評価しない。',
        '新アルゴリズムとしての新規性は支持できない。通常のコード保護・解析研究用である。'
    ).replace('今後は、同一条件のglobal版との差、既存簡約器による復元率・時間、型付き合流の復元誤り、',
        '追加の入出力推定では、baseline/global/per_regionの全42本・1,344制御条件で、各3回の問い合わせによってアフィン式を推定できた。\n'
        '別入力1,438,080出力ペアの照合で不一致は0だった。内部式や元ソースの復元を示したものではない。\n\n'
        '今後は、同一条件のglobal版との差、既存簡約器による復元率・時間、型付き合流の復元誤り、')

def related(text):
    text = text.replace('確認日：2026-10-11。結論は**新規性未確定**。',
        '確認日：2026-10-11。追跡監査の結論は**現状を新アルゴリズムとして採用しない**。\n'
        '候補作成時の調査に、下記の直接的な先行例が不足していた。詳細は [新規性監査](novelty-audit.md) と [検索記録](novelty-search-log.md)。')
    text = text.replace('| [Tigress EncodeData]',
        '| [Fukushimaほか、2006](https://www.jstage.jst.go.jp/article/ipsjdc/2/0/2_0_498/_pdf) §4.1 | 行列とベクトルで複数変数を同時符号化 | 今回の `Av+b` の直接的な先行例。剰余環の条件は区別する |\n'
        '| [Slicing Obfuscations、2007](https://www.cs.auckland.ac.nz/~cthombor/Pubs/drm0127-majumdar.pdf) §5.3 | 領域ごとに別符号化、境界の復号・符号化の式を合成 | **今回の領域別切替という中核にも先行例がある** |\n'
        '| [Tigress EncodeData]', 1)
    return text.replace('これは研究仮説であり、「既存研究にないアルゴリズムを発明した」という結果ではない。',
        'これは候補提示時の研究仮説であり、「既存研究にないアルゴリズムを発明した」という結果ではない。\n'
        '追跡監査で中核の重複が判明した。限定した入出力解析でも領域別切替の問い合わせ数の利点は示されなかった。')

def experiment(text):
    head, rest = text.split('\n', 1)
    return head + '\n\n> 追記：この報告は生成時の正しさ・サイズ検証であり、新規性や解析耐性を示さない。\n' \
        '> 追加した42本の入出力解析と、先行研究との重複判断は [新規性監査](novelty-audit.md) を参照。\n' + rest

update('README.md', readme)
update('docs/design.md', design)
update('docs/related-work.md', related)
update('docs/experiment-report.md', experiment)
(stage / 'updates.json').write_text(json.dumps(changes, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'staged_updates': list(changes)}, ensure_ascii=False))
