"""Build frozen local/established optimizer comparisons; no Wasm instantiation."""
import hashlib
import json
import re
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

from normalize_wat_local import normalize
from prepare_followup_controlled import separate_function_closures
from analyze_corpus import analyze
from audit_normalization_signatures import signatures
from audit_normalization_resources import resources,canonical

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'
WABT=ROOT/'.tools/wabt-1.0.42/bin'
OPT=ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    p=subprocess.run([str(a) for a in args],capture_output=True,text=True,encoding='utf-8',timeout=180)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout


def wat(path,named=False):
    return command(WABT/'wasm2wat.exe',path,'--generate-names' if named else '--no-debug-names')


def transform(source,target,method,debug=False):
    """Shared implementation also processes provenance-only auxiliary inputs."""
    events=[]
    if method['kind']=='copy':shutil.copyfile(source,target)
    elif method['kind']=='local':
        text=separate_function_closures(wat(source,True));result,events=normalize(text,tuple(method['rules']))
        textpath=target.with_suffix('.wat');textpath.write_text(result,encoding='utf-8')
        args=[WABT/'wat2wasm.exe',textpath,'-o',target]
        if debug:args.append('--debug-names')
        command(*args)
    elif method['kind']=='binaryen':
        command(OPT,source,*method['flags'],*(['-g'] if debug else []),'-o',target)
    else:raise ValueError(method)
    command(WABT/'wasm-validate.exe',target)
    return events


def read_plan():
    path=OUT/'normalization-plan.json';plan=json.loads(path.read_text(encoding='utf-8'))
    assert plan['frozen_before_execution'] and plan['labels']==77
    for row in plan['required_sources']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    for row in plan['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    return path,plan


def main():
    plan_path,plan=read_plan();target=OUT/'normalization-static.json';assert not target.exists()
    build=OUT/'normalization-artifacts';assert not build.exists();build.mkdir()
    rows=[];preparations=[]
    status=dict(status='running',records=rows,preparations=preparations,plan_sha256=sha(plan_path),runtime_executed=False)
    def save():
        (build/'progress.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    try:
        for item in plan['inputs']:
            source=ROOT/item['path'];started=time.perf_counter();original=wat(source)
            presented=separate_function_closures(wat(source,True));pwat=build/(item['id']+'-presentation.wat');pbin=pwat.with_suffix('.wasm')
            pwat.write_text(presented,encoding='utf-8');command(WABT/'wat2wasm.exe',pwat,'-o',pbin)
            assert wat(pbin)==original,'Presentation adapter changed canonical module'
            preparations.append(dict(input_id=item['id'],elapsed_ms=(time.perf_counter()-started)*1000,
                presentation_wasm_sha256=sha(pbin),canonical_equal=True))
            initial_signatures=signatures(source);initial_resources=resources(source.read_bytes())
            for method in plan['methods']:
                output=build/(item['id']+'--'+method['id']+'.wasm');started=time.perf_counter()
                events=transform(source,output,method);text=wat(output)
                preprocessing_ms=(time.perf_counter()-started)*1000
                canonical_path=output.with_suffix('.canonical.wat');canonical_path.write_text(text,encoding='utf-8')
                event_path=output.with_suffix('.events.json');event_path.write_text(json.dumps(events,indent=2)+'\n',encoding='utf-8')
                measured=analyze(dict(object=str(output.relative_to(ROOT)).replace('\\','/'),sha256=sha(output)))
                assert measured['status']=='ok' and measured['valid_wabt']
                sig=signatures(output);res=resources(output.read_bytes())
                exported_functions=canonical(sig['exported_functions'])==canonical(initial_signatures['exported_functions'])
                exported_resources=canonical(res['exported_resources'])==canonical(initial_resources['exported_resources'])
                assert exported_functions and exported_resources,'Exported API type/limit changed'
                all_signatures=all(canonical(sig[k])==canonical(initial_signatures[k]) for k in sig)
                all_resources=all(canonical(res[k])==canonical(initial_resources[k]) for k in ['imported_resources','exported_resources'])
                if method['kind']=='local':assert all_signatures and all_resources
                row=dict(input_id=item['id'],family=item['family'],transformation=item['transformation'],method=method['id'],
                    path=str(output.relative_to(ROOT)).replace('\\','/'),sha256=sha(output),bytes=output.stat().st_size,
                    instruction_count=measured['instruction_count'],opcodes=measured['opcodes'],
                    canonical_path=str(canonical_path.relative_to(ROOT)).replace('\\','/'),canonical_sha256=sha(canonical_path),
                    events=len(events),events_by_rule=dict(Counter(e['rule'] for e in events)),event_log_sha256=sha(event_path),
                    preprocessing_elapsed_ms=preprocessing_ms,
                    timing_scope='Method processing and output write, WABT validation, canonical disassembly. Shared presentation verification and static metrics/API audit are separate.',
                    exported_functions_equal=exported_functions,exported_resources_equal=exported_resources,
                    all_interface_records_equal=all_signatures,imported_resources_equal=canonical(res['imported_resources'])==canonical(initial_resources['imported_resources']),
                    signatures=sig,resources=res,runtime_executed=False)
                rows.append(row);save();print(json.dumps(dict(completed=len(rows),input=item['id'],method=method['id'])),flush=True)
        assert len(rows)==77
        for row in rows:
            ref=next(r for r in rows if r['input_id']==row['family']+'-baseline' and r['method']==row['method'])
            before=next(r for r in rows if r['input_id']==row['input_id'] and r['method']=='unmodified')
            row.update(same_canonical_as_equally_processed_reference=row['canonical_sha256']==ref['canonical_sha256'],
                instruction_ratio_to_unmodified=row['instruction_count']/before['instruction_count'])
        status.update(status='static-validation-complete',unique_output_sha256=len({r['sha256'] for r in rows}),
            evaluator_sha256=sha(Path(__file__)),normalizer_sha256=sha(ROOT/'scripts/normalize_wat_local.py'),
            scope='Development/shared-lineage controls and reviewed published examples; no runtime correctness or throughput claim yet.')
        save();target.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(status=status['status'],records=len(rows),unique_outputs=status['unique_output_sha256'])))
    except Exception as error:
        status.update(status='failed',error=str(error));save();raise


if __name__=='__main__':main()
