"""Create diagnostic counters and bounded helper ablations; never execute Wasm."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'
WABT=ROOT/'.tools/wabt-1.0.42/bin'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    result=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=120,check=True)
    return result.stdout


def fields(text):
    starts=list(re.finditer(r'^  \(',text,re.M))
    rows=[]
    for i,start in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else text.rfind(')')
        rows.append((start.start(),end,text[start.start():end]))
    return rows


def main():
    destination=OUT/'path-plan.json'
    if destination.exists():
        raise RuntimeError('Do not replace frozen path plan')
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    spec=json.loads((ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json').read_text(encoding='utf-8'))
    build=OUT/'path-artifacts';build.mkdir(exist_ok=True)
    texts={};items={};function_sets={}
    for label,method in [('original','xmr-wasm'),('flattening','xmr-wasm-emccobf-flattening'),('substitution','xmr-wasm-emccobf-substitution')]:
        item=next(m for m in spec['modules'] if m['method']==method);items[label]=item
        assert sha(ROOT/item['object'])==item['sha256']
        text=command(WABT/'wasm2wat.exe',ROOT/item['object'],'--generate-names')
        texts[label]=text
        function_sets[label]={re.match(r'  \(func (\$\S+)',body)[1]:body for _,_,body in fields(text) if body.startswith('  (func ')}
        (build/(label+'-original.wat')).write_text(text,encoding='utf-8')
    names=['$hash','$f35','$f111','$f112','$f118','$f113','$f82','$f83','$f86']
    artifacts=[]
    def add_asset(name,relative):
        path=ROOT/relative
        row=dict(name=name,path=str(relative).replace('\\','/'),sha256=sha(path));plan['assets'].append(row);return row
    for label,text in texts.items():
        functions=function_sets[label]
        assert set(names).issubset(functions)
        changed=text
        for name in names:
            body=functions[name];lines=body.splitlines(keepends=True)
            # Generated WAT places all local declarations on the next line.
            insertion=1
            while insertion<len(lines) and lines[insertion].lstrip().startswith('(local '):
                insertion+=1
            counter='$followup_count_'+name[1:]
            lines.insert(insertion,f'    global.get {counter}\n    i64.const 1\n    i64.add\n    global.set {counter}\n')
            assert changed.count(body)==1
            changed=changed.replace(body,''.join(lines),1)
        # Add globals after every original global, preserving original numeric indices.
        export_start=changed.index('  (export ')
        globals_=''.join(f'  (global $followup_count_{name[1:]} (mut i64) (i64.const 0))\n' for name in names)
        exports=''.join(f'  (export "followup_count_{name[1:]}" (global $followup_count_{name[1:]}))\n' for name in names)
        changed=changed[:export_start]+globals_+exports+changed[export_start:]
        wat=build/(label+'-counted.wat');wasm=wat.with_suffix('.wasm');wat.write_text(changed,encoding='utf-8')
        command(WABT/'wat2wasm.exe',wat,'-o',wasm);command(WABT/'wasm-validate.exe',wasm)
        a=add_asset(label+'-counted.wasm',wasm.relative_to(ROOT))
        add_asset(label+'.js',items[label]['glue'])
        artifacts.append(dict(id=label,wasm=a['name'],sha256=a['sha256'],original_sha256=items[label]['sha256'],
            glue=label+'.js',counters=[n[1:] for n in names],original_wat_sha256=sha(build/(label+'-original.wat')),
            adaptation='Append i64 mutable globals/exports; add entry increments after locals only. Original functions, calls and indices retained.'))
    # Diagnostic ablations use the same distributed flattened module, replacing only reviewed XOR bodies.
    ablations=[]
    for label,selected in [('restore-xor8',['$f112']),('restore-xor16',['$f118']),('restore-both',['$f112','$f118'])]:
        changed=texts['flattening']
        for name in selected:
            before=function_sets['flattening'][name];after=function_sets['original'][name]
            assert before.splitlines()[0]==after.splitlines()[0]
            assert 'call ' not in before and 'call ' not in after and 'global.set' not in after
            changed=changed.replace(before,after,1)
        wat=build/(label+'.wat');wasm=wat.with_suffix('.wasm');wat.write_text(changed,encoding='utf-8')
        command(WABT/'wat2wasm.exe',wat,'-o',wasm);command(WABT/'wasm-validate.exe',wasm)
        generated={re.match(r'  \(func (\$\S+)',body)[1]:body for _,_,body in fields(changed) if body.startswith('  (func ')}
        differences=[name for name in generated if generated[name]!=function_sets['flattening'][name]]
        assert set(differences)==set(selected)
        a=add_asset(label+'.wasm',wasm.relative_to(ROOT))
        ablations.append(dict(id=label,wasm=a['name'],sha256=a['sha256'],glue='flattening.js',
            replaced_functions=selected,other_function_bodies_unchanged=True,
            scope='Manual diagnostic helper restoration inside the same flattened module; not automatic normalization or source rebuild.'))
    add_asset('paths.cjs','experiments/runtime-reference/followup-paths.cjs')
    plan['path_diagnostic']=dict(artifacts=artifacts,ablations=ablations,
        vectors=[v for v in plan['public_vectors'] if bytes.fromhex(v['hex'])[0]<7],
        predicted_not_called=['f112','f113'],expected_outputs='published cn/0 vectors',
        use_of_counts='Entry counts only; instruction execution counts and time shares are not inferred.',
        frozen_before_execution=True)
    plan['maximum_wall_seconds']=300
    destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=str(destination),counted=len(artifacts),ablations=len(ablations))))


if __name__=='__main__':
    main()
