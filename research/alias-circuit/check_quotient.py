"""Native-engine checks of all 15 cross-alias patterns and attack rejection controls."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from compile import parse, emit, tool, FEATURES
from attack import partitions, declarations, body, recover

root=Path(sys.argv[1]);out=root/'quotient-check';out.mkdir(exist_ok=False)
m=json.loads((root/'manifest.json').read_text());reports=[]
for row in m['rows']:
    if row['mode']!='alias':continue
    module=parse(tool('wasm-dis',[root/row['wasm']]))
    fs=[x for x in module[1:] if x[0]=='func']
    gate=next(f for f in fs if len(declarations(f,'param'))==2 and
              all(isinstance(x[2],list) for x in declarations(f,'param')))
    pair=declarations(gate,'param')[0][2][-1]
    cell=next(x[1] for x in module[1:] if x[0]=='type' and x[2][0]=='struct' and len(x[2])==2)
    expected=[]
    for i,p in enumerate(partitions(4)):
        locals_=[['local',f'$c{k}',['ref','null',cell]] for k in range(max(p)+1)]
        init=[['local.set',f'$c{k}',['struct.new_default',cell]] for k in range(max(p)+1)]
        ref=lambda k:['ref.as_non_null',['local.get',f'$c{p[k]}']]
        call=['call',gate[1],['struct.new',pair,ref(0),ref(1)],['struct.new',pair,ref(2),ref(3)]]
        f=['func',f'$probe{i}',['result','i32'],*locals_,['local','$answer',['ref','null',pair]],*init,
           ['local.set','$answer',call],['ref.eq',['struct.get',pair,'0',['local.get','$answer']],
                                               ['struct.get',pair,'1',['local.get','$answer']]]]
        module.extend([f,['export',f'"probe{i}"',['func',f'$probe{i}']]])
        expected.append(1-(int(p[0]==p[1])&int(p[2]==p[3])))
    stem=Path(row['wasm']).stem;wp=out/(stem+'.wat');bp=out/(stem+'.wasm')
    wp.write_text(emit(module),encoding='utf-8');tool('wasm-as',[wp,*FEATURES,'-o',bp])
    script='const fs=require("fs");const b=fs.readFileSync(process.argv[1]);if(!WebAssembly.validate(b))throw Error("validate");const e=new WebAssembly.Instance(new WebAssembly.Module(b)).exports;console.log(JSON.stringify(Array.from({length:15},(_,i)=>e["probe"+i]())));'
    actual=json.loads(subprocess.check_output([shutil.which('node'),'-e',script,str(bp)],text=True,timeout=30))
    if actual!=expected:raise AssertionError('Native quotient mismatch')
    reports.append({'wasm':row['wasm'],'expected':expected,'actual':actual})

controls=[]
base=parse(tool('wasm-dis',[root/'mix-alias.wasm']))
for label in ['constant_gate','bad_decoder','uninitialized_scratch']:
    mm=copy.deepcopy(base);fs=[x for x in mm[1:] if x[0]=='func']
    gate=next(f for f in fs if len(declarations(f,'param'))==2 and isinstance(declarations(f,'param')[0][2],list))
    if label=='constant_gate':
        writes=[x for x in body(gate) if x[0]=='struct.set'];writes[1][-1]=copy.deepcopy(writes[0][-1])
    elif label=='bad_decoder':
        dec=next(f for f in fs if len(declarations(f,'param'))==1 and declarations(f,'result')==[['result','i32']])
        eq=body(dec)[0];eq[2]=copy.deepcopy(eq[1])
    else:
        # A dead read still violates the limited abstract interpreter's freshness contract.
        # Use local.tee/assignment so the helper interpreter observes it.
        first_write=next(x for x in body(gate) if x[0]=='struct.set')
        old=body(gate)[2]
        gate.insert(gate.index(old),['local.set',declarations(gate,'local')[-1][1],
          ['struct.get',first_write[1],'0',copy.deepcopy(first_write[3])]])
    wp=out/(label+'.wat');bp=out/(label+'.wasm');wp.write_text(emit(mm),encoding='utf-8')
    tool('wasm-as',[wp,*FEATURES,'-o',bp])
    try:recover(bp,out/(label+'-recovered.wasm'));raise AssertionError('Control accepted')
    except ValueError as e:controls.append({'control':label,'status':'rejected','reason':str(e)})
r={'native_partition_executions':sum(len(x['actual']) for x in reports),'mismatches':0,'reports':reports,'controls':controls}
(out/'results.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='reports'}))
