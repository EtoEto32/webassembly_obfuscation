# -*- coding: utf-8 -*-
import collections,json,pathlib,sys
import run as c

base=(c.ROOT/sys.argv[1]).resolve();deob=(c.ROOT/sys.argv[2]).resolve()
out=(c.ROOT/sys.argv[3]).resolve();out.mkdir(parents=True,exist_ok=False)
rows=json.loads((base/'results.json').read_text(encoding='utf-8'))
ds=json.loads((deob/'results.json').read_text(encoding='utf-8'))
facts={'groups':{},'process_status':dict(collections.Counter(v['process']['status'] for r in rows for v in r['outputs'].values()))}
for group in ('list','scalar'):
    rr=[r for r in rows if r['group']==group];ww=[r['outputs']['wat'] for r in rr]
    facts['groups'][group]={'inputs':len(rr),'original_calls':sum(r['original_check']['calls'] for r in rr),
        'roundtrip_calls':sum(w['check']['calls'] for w in ww),'roundtrip_mismatches':sum(w['check']['mismatches'] for w in ww),
        'roundtrip_traps':sum(w['check']['traps'] for w in ww),'valid_wat':sum(w['validation']['status']=='success' for w in ww)}
facts['privileged_restore']={'calls':sum(r['outputs']['wat'].get('privileged_data_restore_check',{}).get('calls',0) for r in rows),
    'mismatches':sum(r['outputs']['wat'].get('privileged_data_restore_check',{}).get('mismatches',0) for r in rows)}
facts['deob']={'inputs':len(ds),'input_byte_identical':sum(r['input_byte_identical'] for r in ds),
    'calls':sum(r['check']['calls'] for r in ds),'mismatches':sum(r['check']['mismatches'] for r in ds)}
verified=[]
for folder in (base,deob):
    pins=json.loads((folder/'sha256.json').read_text(encoding='utf-8'))
    bad=[p['file'] for p in pins if c.sha(c.ROOT/p['file'])!=p['sha256']]
    if bad:raise RuntimeError(str(bad))
    verified.append({'manifest':c.rel(folder/'sha256.json'),'pins':len(pins),'mismatches':0})
facts['source_verification']=verified
assert facts['process_status']=={'success':81}
assert facts['groups']['list']['roundtrip_mismatches']==504
assert facts['groups']['scalar']['roundtrip_mismatches']==0
assert facts['privileged_restore']=={'calls':5148,'mismatches':0}
assert facts['deob']=={'inputs':18,'input_byte_identical':18,'calls':75906,'mismatches':0}
c.save(out/'summary.json',facts)
report='''# Disrobe v0.10.6の未変換基準と整数式比較

2026-10-23。新発明の提案ではなく、外部解析器による比較の成立範囲を確認した測定。

## 結果

|入力群|入力数|WAT再validation|再実行呼出し|不一致|trap|
|---|---:|---:|---:|---:|---:|
|未変換linked list|9|9|5,148|504|0|
|整数式 plain / repair / aligned、raw / O3|18|18|75,906|0|0|

全27入力のC/JSON/WAT生成81プロセスが正常終了した。timeout・非0終了は0。成功終了と意味一致を分けた結果であり、難読化による解析失敗数ではない。入力の元Wasmは同じ81,054テストで不一致0だった。

リストは8/32/128レコードと3 field配置。出力JSONはdata_segments=1と認識するが、生成WATにはdata segmentがない。各レコードを照会する504呼出しで0が返り、元の非0値と不一致になった。miss照会は一致した。別ファイルに元のdata segmentだけを戻す**正解情報を使った診断**では5,148呼出し全てが一致した。これは回復成功率に含めない。生成WATには元にないmemory上限16とtableもあるため、この診断でも任意モジュールの完全同値性を保証しない。

Cの9出力はすべて、padding64の後にint32_t field_64/68/72を持つDisrobeStructFunction0Heapを宣言した。しかしその型名は宣言の1箇所だけに現れ、lookupはi32の局所変数、wasm_load_i32と固定offsetを使う。nextの再帰record pointer型、stride12のレコード配列、field役割の回復は確認できない。『structという文字列を出した』だけでは型回復成功にしない。C再コンパイル・実行は環境にC compilerがなく未実施。Cの意味誤りとは集計しない。

整数式のWATは18条件すべてで差分テストに一致した。Cには例としてaligned多項式のrem、mask、shiftとSSA風temporaryが残る。外観だけから意味の理解・回復に成功したとは断定しない。別コマンドwasm deobも18入力へ実行し、18出力は入力とbyte一致、75,906呼出し一致だった。主実験で既に既知のword射影がalignedのraw/O3全6条件を元の式へ回復している。したがって、汎用deobが変更しなかったことは強い保護の根拠にならない。

## 条件と再現

Disrobe公式v0.10.6 Windows x86_64配布物。release published_at=2026-09-15T07:39:10Z、archive SHA256=6f073d9330c3c2ae61e5025e5989c5fb4e03a439dffea7c9c4a0a833f4f69aa8。公開SHA256SUMSと一致を確認した。署名の独立検証は実施していない。ツールへ渡したのはWasmのみで、layout正解・元source・入力oracleは渡していない。--no-cache、1プロセスにつき30秒上限。実コマンド、stdout/stderr、入力と出力のhashを保存した。

Windows 10.0.26100 x64、Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42。生成プロセス時間は約13.9–21.9msの単発観測で、ウォームアップ・反復による性能比較ではない。新変換の実行性能・メモリ効果の測定ではない。

リポジトリrootから、既存と異なる出力名を指定する。

```powershell
python research/disrobe-baseline/run.py results/disrobe-reproduction
python research/disrobe-baseline/deob.py results/disrobe-deob-reproduction results/disrobe-reproduction
python research/disrobe-baseline/report.py results/disrobe-reproduction results/disrobe-deob-reproduction results/disrobe-report-reproduction
```

前提入力はresults/invention-20261021/notdec-baseline-v1とresults/invention-20261023/residue-wrap-v2。生成方法は各research/notdec-baseline、research/residue-wrapにある。新たな任意入力対応CLIではなく、固定評価セットの再現スクリプトである。出力先が存在すれば停止する。

## 研究判断

Disrobeは今回の整数式の可読化出力・正常実行確認には利用できる。リストの一括復元成功率や型回復率を本方式の解析耐性の主要指標にするには、未変換の正答基準を満たしていない。NotDecは依然未実行であり、本結果をNotDecの結果へ置き換えない。今回新しい難読化原理や特許上の新規性を確立したとは主張しない。先行する方式別の適応解除を引き続き必要条件にする。

## 一次資料

- [Disrobe v0.10.6 release](https://github.com/1-3-7/disrobe/releases/tag/v0.10.6)：公式配布物とchecksum。
- [Disrobe repository](https://github.com/1-3-7/disrobe)：ツールの目的。今回は同梱READMEとCLI helpを閲覧し、該当実装のsource codeは未精読。
- [整数剰余の自前適応解析](../../../research/residue-wrap/README.md)：別実験。Disrobe著者の実装や論文の実験ではない。

査読済み論文の比較とは区別する。外部投稿・issue作成・public uploadは行っていない。
'''
(out/'report.md').write_text(report,encoding='utf-8')
c.save(out/'sha256.json',[{'file':c.rel(p),'sha256':c.sha(p)} for p in [c.HERE/'report.py']+list(out.rglob('*')) if p.is_file()])
print(json.dumps(facts))
