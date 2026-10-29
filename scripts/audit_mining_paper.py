"""Check manuscript statistics against saved data and save claim provenance."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mining-methods'


def main():
    summary=list(csv.DictReader((OUT/'method-summary.csv').open(encoding='utf-8')))
    pairs=list(csv.DictReader((OUT/'pair-metrics.csv').open(encoding='utf-8')))
    tex=(ROOT/'paper/main.tex').read_text(encoding='utf-8-sig')
    claims=[]
    def metric(method,metric,release,expected,statistic='ratio',field='median'):
        r=next(r for r in summary if r['method']==method and r['metric']==metric and r['release']==release and r['statistic']==statistic)
        observed=float(r[field])
        assert abs(observed-expected)<=.000501,(method,metric,release,observed,expected)
        claims.append(dict(section='RQ2 static structure comparison',claim=f'{method}/{metric}/{release}/{statistic}/{field}',value=observed,
                           printed_value=expected,source='results/mining-methods/method-summary.csv',selector={k:r[k] for k in ('method','metric','release','statistic')}))
    for m,vals in {
      'tigress/encodearithmetic':(2.515,1.655), 'tigress/virtualize':(1.417,1.418),
      'llvm/subobf':(1.461,1.327), 'llvm/funcwra':(1.006,1.005),
      'wasm-mutate/iteration-series':(1.395,1.350)}.items():
        for release,v in zip(('binaries','binaries-opt'),vals):metric(m,'instruction_count',release,v)
    for m,release,v in [('tigress/encodearithmetic','binaries',2.601),('llvm/subobf','binaries',1.477),
                         ('tigress/virtualize','binaries',1.834),('tigress/virtualize','binaries-opt',2.322),
                         ('wasm-mutate/iteration-series','binaries',1.396),('wasm-mutate/iteration-series','binaries-opt',1.330)]:
        metric(m,'bytes',release,v)
    for m,med,lo,hi in [('llvm/cffobf',1.098,1.088,1.439),('tigress/flatten',1.394,1.387,1.407),('tigress/encodearithmetic',2.515,2.202,2.773)]:
        for f,v in [('median',med),('minimum',lo),('maximum',hi)]:metric(m,'instruction_count','binaries',v,field=f)
    fields=['defined_functions','br_table_in_loop_count','call_count','call_indirect_count','memory_load_count','memory_store_count']
    for method,unopt,opt in [
      ('antialiasanalysis',[33,0,-218,358,2361,6290],[69,0,-185,358,2201,6297]),
      ('encodearithmetic',[-1,0,-1,0,12834.5,5997],[1,0,0,0,3392,5997]),
      ('flatten',[-1,70,-1,0,72,6733],[1,70,1,0,101,6743]),
      ('virtualize',[-1,91.5,-1,0,1150.5,6967.5],[1,98,0,0,218.5,6968.5])]:
        for release,values in [('binaries',unopt),('binaries-opt',opt)]:
            for field,value in zip(fields,values):metric('tigress/'+method,field,release,value,statistic='delta')
    assert len(pairs)==20460
    assert all(r['name_before']=='False' and r['name_after']=='False' for r in pairs)
    for release,values in [('binaries',[310503,573954,263451,165827,97625]),('binaries-opt',[140103,324681,184578,86969,97598])]:
        r=next(r for r in pairs if r['release']==release and r['program']=='cn-0' and r['method']=='tigress/virtualize')
        for key,v in zip(['bytes_before','bytes_after','bytes_delta','code_section_bytes_delta','data_section_bytes_delta'],values):
            assert float(r[key])==v
            assert f'{v:,}' in tex
            claims.append(dict(section='RQ2 code/data section comparison',claim=f'cn-0/virtualize/{release}/{key}',value=v,
                               source='results/mining-methods/pair-metrics.csv',path=r['path'],sha256=r['sha256'],baseline_sha256=r['baseline_sha256']))
    bykey={(r['release'],r['program'],r['method']):r for r in pairs}
    matched=0
    for (rel,p,m),r in bykey.items():
        if m=='tigress/antitaintanalysis':
            assert r['sha256']!=bykey[(rel,p,'tigress/randomfuns')]['sha256'];matched+=1
    assert matched==20
    for m in ('antitaintanalysis','randomfuns'):metric('tigress/'+m,'instruction_count','binaries',1.332)
    features=list(csv.DictReader((OUT/'dataset-feature-context.csv').open(encoding='utf-8')))
    for cohort,values in [('minesweeper/miner_samples',[33.33,100,54.55]),('swamped/Cryptojackers_43',[42.86,100,57.14]),
                         ('wasmmal/malware',[46.07,98.88,59.57]),('wasmmal/benign',[52.77,81.85,20.27]),('wasmbench/filtered_release',[56.66,82.73,25.79])]:
        r=next(r for r in features if r['cohort']==cohort)
        for key,v in zip(['br_table_in_loop_count_present_percent','call_indirect_count_present_percent','nop_count_present_percent'],values):
            assert abs(float(r[key])-v)<.0051
            claims.append(dict(section='tab:features',claim=f'{cohort}/{key}',value=float(r[key]),printed_value=v,
                               denominator=int(r['analyzed_ok']),source='results/mining-methods/dataset-feature-context.csv'))
    mechanism=json.loads((OUT/'mechanism-evidence.json').read_text())
    for r in mechanism['claims']:
        claims.append(dict(section='RQ1 selected mechanism cases',claim=r['id'],interpretation=r['status'],
                           source='results/mining-methods/mechanism-evidence.json',selector=r['id'],
                           independent_human_review='required'))
    claims += [dict(section='tab:settings',claim='Proof-of-Theft 34 directory settings across9 types; not prevalence',
                    source='results/mining-methods/proof-of-theft-declared-settings.csv'),
               dict(section='RQ1 instrumentation controls',claim='Prior instrumentation controls and8 exploratory cases',
                    source='results/rq-validation/review-ledger.json',note='Methodological controls, not mining mechanism prevalence')]
    (OUT/'paper-claim-evidence.json').write_text(json.dumps(claims,indent=2),encoding='utf-8')
    assert '\\item[RQ1] 公開WebAssembly採掘データセット' in tex
    assert '\\item[RQ2] 難読化はハッシュ出力の正しさ' in tex
    assert '追加のローカル反復測定の13バイナリ' in tex
    assert '未測定' in tex and '最適化条件が異なる' in tex
    bibliography=(ROOT/'paper/references.bib').read_text(encoding='utf-8')
    keys=set(re.findall(r'@\w+\s*\{\s*([^,\s]+)',bibliography))
    cited={k.strip() for group in re.findall(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}',tex) for k in group.split(',')}
    assert not (cited-keys),('missing citation keys',sorted(cited-keys))
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels)),'Duplicate labels'
    referenced=set(re.findall(r'\\(?:ref|pageref)\{([^}]+)\}',tex))
    assert not (referenced-set(labels)),('missing source labels',sorted(referenced-set(labels)))
    graphics=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex)
    for name in graphics:
        target=ROOT/'paper'/name
        assert target.is_file() or target.with_suffix('.pdf').is_file(),name
    report=dict(status='static checks passed; compilation and layout unverified',claim_entries=len(claims),
        scope='Saved static metrics, current RQ wording, citation keys, source labels and figure existence only; not PDF verification or semantic peer review.',
        paper_sha256=hashlib.sha256((ROOT/'paper/main.tex').read_bytes()).hexdigest(),
        bibliography_sha256=hashlib.sha256((ROOT/'paper/references.bib').read_bytes()).hexdigest(),
        checks=['saved program-level static metrics checked','cn-0 section deltas checked',
                'feature percentages checked','current mining RQs and qualified runtime scope present',
                'citation keys, labels and figure files present'],
        compilation_verified=False,page_count_verified=False,
        historical_log_policy='Existing main.log/main.pdf are not proof of compilation of the current source; no historical page count is accepted.',
        remaining='Current built-in compilation, final rendered 6-8 pages, human interpretation review and pending experiments.')
    compilation_path=OUT/'current-compilation.json'
    if compilation_path.exists():
        compilation=json.loads(compilation_path.read_text(encoding='utf-8'))
        verified=(compilation.get('source_sha256')==report['paper_sha256']
                  and compilation.get('bibliography_sha256')==report['bibliography_sha256']
                  and compilation.get('pdf_sha256')==hashlib.sha256((ROOT/'paper/main.pdf').read_bytes()).hexdigest()
                  and compilation.get('log_sha256')==hashlib.sha256((ROOT/'paper/main.log').read_bytes()).hexdigest()
                  and compilation.get('compilation_verified') is True)
        if verified:
            report.update(status='static checks passed; current local compilation verified',
                          compilation_verified=True,page_count_verified=True,
                          pages=compilation['pages'],compilation_evidence='results/mining-methods/current-compilation.json',
                          remaining='Shorten current 15-page manuscript to 6-8 pages; human interpretation review and pending experiments.')
    (OUT/'paper-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    if '\\label{tab:structure}' not in (ROOT/'paper/main.tex').read_text(encoding='utf-8'):
        from audit_compact_mining_paper import main as compact_main
        compact_main()
    else:
        main()
