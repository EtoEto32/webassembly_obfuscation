"""Add per-call-site diagnostics to separate helper frequency by caller/loop."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'
WABT=ROOT/'.tools/wabt-1.0.42/bin'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination=OUT/'callsite-plan.json'
    if destination.exists():raise RuntimeError('Preserve frozen diagnostic plan')
    plan=json.loads((OUT/'path-plan.json').read_text(encoding='utf-8'))
    build=OUT/'callsite-artifacts';build.mkdir(exist_ok=True);artifacts=[];inventory=[]
    for old in plan['path_diagnostic']['artifacts']:
        source=OUT/'path-artifacts'/(old['id']+'-counted.wat')
        text=source.read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
        output=[];function=None;scopes=[];sites=[]
        for number,line in enumerate(lines,1):
            header=re.match(r'^  \(func (\$\S+)',line)
            if header:function=header[1];scopes=[]
            elif line.startswith('  ('):function=None;scopes=[]
            token=line.strip().rstrip(')')
            if function:
                if token.startswith(('block ','loop ','if ')) or token in ['block','loop','if']:
                    scopes.append(token)
                elif token=='end' and scopes:scopes.pop()
                if token=='call $f118':
                    name='site_'+str(len(sites)).zfill(3)
                    output.extend([f'    global.get $followup_count_{name}\n', '    i64.const 1\n',
                        '    i64.add\n',f'    global.set $followup_count_{name}\n'])
                    sites.append(dict(counter=name,caller=function,source_line=number,callee='$f118',enclosing_constructs=scopes.copy()))
            output.append(line)
        assert sites
        generated=''.join(output);insertion=generated.index('  (export ')
        definitions=''.join(f'  (global $followup_count_{s["counter"]} (mut i64) (i64.const 0))\n' for s in sites)
        exports=''.join(f'  (export "followup_count_{s["counter"]}" (global $followup_count_{s["counter"]}))\n' for s in sites)
        generated=generated[:insertion]+definitions+exports+generated[insertion:]
        wat=build/(old['id']+'-sites.wat');wasm=wat.with_suffix('.wasm');wat.write_text(generated,encoding='utf-8')
        subprocess.run([str(WABT/'wat2wasm.exe'),str(wat),'-o',str(wasm)],check=True,capture_output=True,timeout=60)
        subprocess.run([str(WABT/'wasm-validate.exe'),str(wasm)],check=True,capture_output=True,timeout=60)
        name=old['id']+'-sites.wasm';plan['assets'].append(dict(name=name,path=str(wasm.relative_to(ROOT)).replace('\\','/'),sha256=sha(wasm)))
        artifact=dict(old);artifact.update(wasm=name,sha256=sha(wasm),counters=old['counters']+[s['counter'] for s in sites],
            adaptation='Retain entry counters and insert balanced i64 global increments immediately before each direct call to f118; all original argument stack values remain below the temporary counter values.')
        artifacts.append(artifact);inventory.append(dict(id=old['id'],source_path=str(source.relative_to(ROOT)),source_sha256=sha(source),sites=sites))
    plan['path_diagnostic'].update(artifacts=artifacts,ablations=[],callsite_inventory=inventory,
        interpretation='Per-direct-call-site counters and helper entry counters. Any deficit between site sum and entry count must be reported, not silently treated as zero.',
        original_main_loop_reference='Existing lexical review identifies loop L17 in original f111; do not transfer loop names blindly to other variants.')
    destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'callsite-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([dict(id=r['id'],direct_callsites=len(r['sites']),callers=sorted({s['caller'] for s in r['sites']})) for r in inventory],indent=2))


if __name__=='__main__':main()
