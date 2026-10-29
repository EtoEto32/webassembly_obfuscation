# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import shutil
import sys
from shared import h


def main(out):
    root=h.ROOT;base=root/'results/invention-20261023';out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('report output must be empty')
    out.mkdir(parents=True,exist_ok=True)
    read=lambda folder,file:json.loads((base/('boolean-feedback-'+folder)/file).read_text(encoding='utf8'))
    catalog=read('catalog-v1','summary.json');word=read('word-runtime-v1','summary.json');wordatt=read('word-attack-main-v1','attacks.json');wordmeta=read('word-v1','manifest.json')
    coupled=read('coupled-runtime-v1','summary.json');attacks=read('coupled-attack-v1','attacks.json');meta=read('coupled-v1','manifest.json')
    lines=['# Boolean残差補正：分類・Wasm実装・実測','',
           '2026-10-23。bitwise、整数持上げ、任意切替による群結合を順に検査した。同一候補の3設計段階であり、独立した3発明ではない。有限収束の具体的な構成知見は保存するが、主特許候補には不採用。研究全体は継続する。','',
           f'補正器分類：{catalog["feedback_maps"]:,}個を全{catalog["triangular_maps"]}個の三角Fで検査し、{catalog["valid_count"]:,}個が合格、厳密prefix進行条件は{catalog["prefix_count"]:,}個。失敗時はそのNの検査を打切るためN/F検査総数は{catalog["pair_checks"]:,}。合格一覧SHA256 `{catalog["valid_codes_sha256"]}`。','',
           '## 整数持上げ','', '|関数|方式|O3 bytes|実行中央値 ns|回復 ms（O3）|変換 ms|','|---|---|---:|---:|---:|---:|']
    for r in word['targets']:
        ar=next((a for a in wordatt if a['name']==r['name'] and a.get('optimization',a.get('opt')) in ('O3','-O3')),None) if r['mode']=='feedback' else None
        tr=next((a for a in wordmeta if a['name']==r['name'] and a['mode']==r['mode'] and a['initial']==[0,0,0]),None)
        lines.append('|'+ '|'.join([r['name'],r['mode'],str(r['core_bytes']),f'{r["median_ns"]:.3f}',f'{ar["analysis_ms"]:.3f}' if ar else '対象外',f'{tr["elapsed_ms"]:.3f}' if tr else '対象外'])+'|')
    lines+=['','wordの全6保護条件を公開更新式の部分木候補から回復。読取りと出力生成を除く単回解析時間。旧word-attack-v1 smokeは出力生成を含む古い時間尺度なので表から除外した。','',
            '## 任意切替による群結合','', '|関数|方式|O3 bytes|実行中央値 ns|新解析 ms（O3）|変換 ms|','|---|---|---:|---:|---:|---:|']
    for r in coupled['targets']:
        ar=next((a for a in attacks if a['name']==r['name'] and a['mode']==r['mode'] and a['optimization']=='-O3'),None)
        tr=next((a for a in meta if a['name']==r['name'] and a['mode']==r['mode']),None)
        lines.append('|'+ '|'.join([r['name'],r['mode'],str(r['core_bytes']),f'{r["median_ns"]:.3f}',f'{ar["analysis_ms"]:.3f}' if ar else '対象外',f'{tr["elapsed_ms"]:.3f}' if tr else '対象外'])+'|')
    lines+=['','固定補正を小SCCから消去する旧解析は5.60/4.57/13.56msと、新解析より速い。上表は同じ新解析器で対照をそろえた比較であり、固定版の最強攻撃費用として使わない。切替版の最大SCCは6/9/10語。旧解析の未対応6件は保護成功から除外し、新解析は全12条件を回復した。','',
            '## 正当性・監査の範囲','', '|実験|実測|','|---|---|']
    for folder,label,field in [('main-v1','bitwise主','total_calls'),('word-v1','word主','calls'),('word-attack-main-v1','word回復','calls'),('coupled-v1','切替主','total_calls'),('coupled-attack-v1','切替・固定の新解析回復','total_calls')]:
        c=read(folder,'correctness.json');assert c['mismatches']==0;lines.append(f'|{label}|{c[field]:,}呼出し、不一致0|')
    audit=read('coupled-audit-v1','audit.json');cross=read('coupled-audit-v1','certificate-crosscheck-v2.json');fa=read('family-audit-v1','audit.json')
    lines+=['|bitwise監査|6byte再現、12回復モデルSMT UNSAT、scratch3,072呼出し|','|word監査|6byte再現、6回復モデルSMT UNSAT、WABT72呼出し、内部rotate反例|',
            f'|切替監査|{audit["byte_replays"]}byte再現、12回復モデルSMT UNSAT、scratch{audit["scratch"]["calls"]:,}呼出し|',
            f'|切替族の別検査|rank {fa["rank_witnesses"]}件、辺{fa["edges_checked"]:,}本、WABT {fa["wabt_calls"]}呼出し|',
            f'|意味上の部分系証明器|独立graph列挙と{cross["cases"]}条件一致（合格{cross["accepted"]}、不合格{cross["rejected"]}）|','',
            '入力再利用・回復版の再実行を独立標本数として合算しない。SMTは元sourceと回復版のpure式モデルを検査するもので、変換器全体を機械的に形式証明した意味ではない。内部rotate、短いround、単独では正しいNを不適切に切り替えるcycleの反例を保存した。','',
            '## 測定条件と限界','',
            'Windows x64、Intel Core i9-11900K、Python3.9.0、Node24.15.0/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Z3 4.13.3。wordと切替の各測定は36fresh process×7batch。warmup16,384、20ms校正、全252batchが10ms以上。V8 --no-liftoff --no-wasm-lazy-compilation。coreのO3後に共通Wasmループを追加し、二度目の全体最適化は行わない。相関したLCG/rotate入力で、独立一様乱数入力ではない。process中央値の中央値を用い、全batch・ばらつき・RSSをraw.jsonへ保存した。','',
            'wordのlogical memoryは全方式0、bitwise/切替は65,536bytesでplainは0。Node peak RSSはprocess全体であり、関数単体の追加物理メモリではない。変換時間はWasm読取り・WAT生成・WABTコンパイル・validateを含む単回値。性能は小規模3関数で一般化できず、同程度のコストに調整した既存製品との優劣は未測定。','',
            '## 不採用理由','',
            '可逆codecを使わないこと、固定点が一意であること、SCCが大きくなることはいずれも保護成功を保証しなかった。wordでは元演算の部分木、切替では任意外部stateに安定する小部分の探索が回復経路となった。切替の追加解析費用は同じ解析器で約3倍、追加実行費用約3.5–3.7倍。既知のnilpotent dynamics、T-functions、切替安定性との独立した新規性も未確立。','',
            '再現手順・読了範囲・論証はresearch/boolean-feedback/README.md、word-lifting-plan.md、coupled-results.md、prior-art.md。ローカルのみに保存しpush・外部公開は行っていない。','']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
    # Snapshot task sources and their local imports; .tools stays in the repository.
    for folder in ('boolean-feedback','hidden-filtration','connectivity-elimination','bit-feedback','stack-cycle','span-mask'):
        for src in (root/'research'/folder).iterdir():
            if src.is_file() and src.suffix in ('.py','.cjs','.md'):
                dest=out/'sources'/src.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    folders=[p for p in base.iterdir() if p.is_dir() and p.name.startswith('boolean-feedback-') and p!=out]
    pins={}
    for folder in folders+[out]:
        for p in folder.rglob('*'):
            if p.is_file():pins[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'pins.json').write_text(json.dumps(pins,indent=2));checked=0
    for rel,digest in pins.items():assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest;checked+=1
    print(json.dumps({'report':str(out/'report.md'),'pinned_files':checked,'result_directories':len(folders)}))

if __name__=='__main__':main(sys.argv[1])
