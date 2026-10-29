"""Reuse pinned SWAMPED transforms across three existing input implementations."""
import ast
import hashlib
import json
import re
from pathlib import Path
import subprocess

from evaluate_seeded_normalization import generate, FUNCTIONS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'
WABT=ROOT/'.tools/wabt-1.0.42/bin'
SOURCE=ROOT/'data/source/swamped/code_perturbation.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
    result=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def separate_function_closures(text):
    """Keep function delimiters outside the upstream line-based instruction adapter."""
    matches=list(re.finditer(r'^  \(',text,re.M));output=[];last=0
    for i,match in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else text.rfind(')')
        field=text[match.start():end]
        if field.startswith('  (func '):
            body=field.rstrip();assert body.endswith(')')
            output.extend([text[last:match.start()],body[:-1]+'\n  )\n']);last=end
    output.append(text[last:]);return ''.join(output)


def main():
    target=OUT/'controlled-generation-v2.json'
    if target.exists():
        raise RuntimeError('Preserve frozen generation manifest')
    expected=json.loads((ROOT/'results/runtime-mining/cross-dataset/swamped/controlled-pair-manifest.json').read_text())
    assert sha(SOURCE)==expected['source_sha256']
    selected=[node for node in ast.parse(SOURCE.read_text(encoding='utf-8')).body
              if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS.values()]
    assert len(selected)==2
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    spec=json.loads((ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json').read_text())
    inputs=[dict(family='swamped',path='results/runtime-mining/cross-dataset/swamped/046dc081-roundtrip.wasm')]
    for family in ['xmr-wasm','webminerpoolhashcn']:
        item=next(m for m in spec['modules'] if m['method']==family)
        inputs.append(dict(family=family,path=item['object']))
    failed=OUT/'controlled-artifacts/xmr-wasm-constsplit.wat'
    if failed.exists() and not (OUT/'controlled-adapter-first-failure.json').exists():
        result=subprocess.run([str(WABT/'wat2wasm.exe'),str(failed),'--no-check','-o',str(OUT/'controlled-artifacts/failed-check.wasm')],capture_output=True,text=True,timeout=120)
        (OUT/'controlled-adapter-first-failure.json').write_text(json.dumps(dict(
            failed_wat_path=str(failed.relative_to(ROOT)),failed_wat_sha256=sha(failed),
            compiler_exit_code=result.returncode,compiler_stderr=result.stderr,
            cause='The existing line-based adapter included final function delimiters in constant instruction lines. Some transformed final constants lost the closing delimiter. Preserve first attempt and separate delimiters in the revised adapter.',
            revision='controlled-artifacts-v2; upstream transform function bodies unchanged'),indent=2)+'\n',encoding='utf-8')
    build=OUT/'controlled-artifacts-v2';build.mkdir(exist_ok=True)
    rows=[]
    for item in inputs:
        original=ROOT/item['path'];text=separate_function_closures(run(WABT/'wasm2wat.exe',original,'--generate-names'))
        for method in ['baseline','nop','constsplit']:
            if method=='baseline':
                generated,changes,excluded=text,[],[]
            else:
                generated,changes,excluded=generate(text,selected,method,20261016,.10)
            name=item['family']+'-'+method;wat=build/(name+'.wat');wasm=wat.with_suffix('.wasm')
            wat.write_text(generated,encoding='utf-8');run(WABT/'wat2wasm.exe',wat,'-o',wasm);run(WABT/'wasm-validate.exe',wasm)
            log=build/(name+'-generation.json');log.write_text(json.dumps(dict(changes=changes,excluded_floating_constant_functions=excluded),indent=2),encoding='utf-8')
            rows.append(dict(id=name,family=item['family'],method=method,
                path=str(wasm.relative_to(ROOT)).replace('\\','/'),sha256=sha(wasm),bytes=wasm.stat().st_size,
                input_path=item['path'],input_sha256=sha(original),wat_sha256=sha(wat),
                generation_log=str(log.relative_to(ROOT)).replace('\\','/'),generation_log_sha256=sha(log),
                transformed_functions=len(changes),tagged_rows=sum(len(c['changes']) for c in changes),
                changed_sites=sum(len(c['changes']) for c in changes)//(3 if method=='constsplit' else 1),
                excluded_floating_constant_functions=excluded,seed=20261016,ratio=0 if method=='baseline' else .10))
    result=dict(status='generated-and-wabt-validated-not-executed',cases=rows,
        source_url=expected['source_url'],source_sha256=sha(SOURCE),adapter_sha256=sha(ROOT/'scripts/evaluate_seeded_normalization.py'),
        generator_sha256=sha(Path(__file__)),wabt_version=run(WABT/'wat2wasm.exe','--version').strip(),
        normalization_applied=False,counting='Constant splitting has three tagged output rows per replacement site; NOP has one tagged row per insertion site. v1 manifest counted tagged rows in its changed_sites field; preserved as history.',
        delimiter_adaptation='Separate final function parentheses from instruction lines before using the existing adapter; no upstream transform-body changes.',
        scope='Same pinned binary-level transforms and WABT pipeline across three existing implementations. Shared CryptoNight/OpenAES lineage remains; not three independent algorithm families.',
        baseline_control='Every variant is compared with its own WAT-roundtrip baseline, not an original with a different encoding pipeline.')
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:r[k] for k in ['id','bytes','transformed_functions','changed_sites']} for r in rows],indent=2))


if __name__=='__main__':
    main()
