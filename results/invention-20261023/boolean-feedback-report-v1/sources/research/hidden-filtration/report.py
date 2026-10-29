import hashlib
import json
from pathlib import Path
import shutil
import sys
import prototype as p


def main(out):
    base=p.ROOT/'results/invention-20261023';out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    folders=['hidden-filtration-main-v1','hidden-filtration-adaptive-v1','hidden-filtration-audit-v1','hidden-filtration-runtime-v1'];checked=0
    for name in folders:
        for file,digest in json.loads((base/name/'pins.json').read_text()).items():
            assert hashlib.sha256((p.ROOT/file).read_bytes()).hexdigest()==digest,file;checked+=1
    main=json.loads((base/folders[0]/'experiment.json').read_text());attacks=json.loads((base/folders[1]/'attacks.json').read_text());runtime=json.loads((base/folders[3]/'summary.json').read_text());verify=json.loads((base/'hidden-filtration-verify-v1/verification.json').read_text())
    lines=['# 有限回更新系の測定結果','', '3つの手作りpure i32関数、seed 20261023。特許の主案としては不採用。全回復だけを理由とせず、先行技術との差、追加実行費用、方式既知解析の費用を合わせて判断した。','',
    '|関数|方式|O3 bytes|実行中央値 ns|回復時間 ms（O3）|変換 ms|','|---|---|---:|---:|---:|---:|']
    for r in runtime['targets']:
        ar=next((a for a in attacks if a['name']==r['name'] and a['mode']==r['mode'] and a['optimization']=='-O3'),None)
        tr=next((a for a in main['transformations'] if a['name']==r['name'] and a['mode']==r['mode']),None)
        values=[r['name'],r['mode'],str(r['core_bytes']),f'{r["median_ns"]:.3f}',f'{ar["analysis_ms"]:.3f}' if ar else '対象外',f'{tr["elapsed_ms"]:.3f}' if tr else '対象外'];lines.append('|'+ '|'.join(values)+'|')
    lines+=['','回復時間は公開binary読取り・kernel照合を除く単回値。raw/O3の両方で回復。一次解析で停止したときだけ二次へ進む。読取り時間と全段階ログはadaptive-v1/attacks.jsonに保存。変換時間は生成、WAT出力、WABTコンパイル・検証を含む単回値。','', '|関数|非線形/線形 実行比|非線形/線形 解析時間比|非線形/元版 実行比|','|---|---:|---:|---:|']
    for name in ('mix8','select10','chain12'):
        rs={r['mode']:r for r in runtime['targets'] if r['name']==name};aa={a['mode']:a for a in attacks if a['name']==name and a['optimization']=='-O3'}
        lines.append(f'|{name}|{rs["nonlinear"]["median_ns"]/rs["linear"]["median_ns"]:.2f}|{aa["nonlinear"]["analysis_ms"]/aa["linear"]["analysis_ms"]:.2f}|{rs["nonlinear"]["median_ns"]/rs["plain"]["median_ns"]:.1f}|')
    lines+=['','解析時間比の増加は測定できた限定効果。ただし小さい例で数秒以内、共通評価器の費用が大きく、同じ費用へ調整した既存難読化法より有利との証拠ではない。独立した新規性の確立にもならない。','',
    f'正当性：主実験 {main["correctness"]["total_calls"]:,} 呼出し不一致0。追加の現行解析器回復版153,828呼出し不一致0、scratch試験4,608、WABT96。これらの同一入力の再実行を独立標本数としてまとめては報告しない。SMTは回復18個のモデル全てUNSAT。', '',
    f'性能：{runtime["processes"]}独立process、{runtime["batches"]} batch、10ms未満 {runtime["batches_under_10ms"]}。warmup16,384、7batch/process、process中央値の中央値。V8 --no-liftoff --no-wasm-lazy-compilation、コアO3後の共通Wasmループ。plainは約1.2–1.5ns/callで、wrapper/JITの影響を含む測定。入力は相関したLCG/rotate列で、独立一様乱数ではない。','',
    'Wasm論理memory：変換3方式は各65,536 bytes、plainは0。Node peak RSSは約35,768–36,172 KiBでprocess全体の値。単一関数の真の追加物理memoryとは解釈しない。全batch、RSS、校正履歴はruntime-v1/raw.jsonに保存。','',
    '歴史的main-v1の36解析は回復24・辞書停止6・timeout6。現行adaptiveは18/18回復（24試行）、timeout0、crash0、未対応0。密な消去から疎な消去へ変更するとtimeoutだった非線形chain12も約4.75秒で回復した。prune試行は有効でなかった。','',
    f'保存済みhash照合 {checked} 件。生成コード・解析器のsnapshotはsources/。元から存在するpaper/main.texとpaper/README.mdは変更していない。','']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8');(out/'sources').mkdir()
    for src in p.HERE.iterdir():
        if src.is_file():shutil.copyfile(src,out/'sources'/src.name)
    for rel in ('research/connectivity-elimination/prototype.py','research/connectivity-elimination/recover.py','research/span-mask/performance.py','research/span-mask/bench.cjs'):
        dest=out/'shared'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p.ROOT/rel,dest)
    (out/'pins.json').write_text(json.dumps({str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2));print(json.dumps({'pins_checked':checked,'report':str(out/'report.md')}))

if __name__=='__main__':main(sys.argv[1])
