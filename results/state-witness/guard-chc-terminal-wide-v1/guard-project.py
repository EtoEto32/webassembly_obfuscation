"""Known cone-of-influence projection for the closed constant-bulk profile."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('witness',HERE/'guard-witness.py');w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
def project(model,left,right):
    # Validate original bit vectors even when all differing bits will be removed.
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('segment state length')
        if any(live and not s['initialLive'] for live,s in zip(side,model['segments'])):raise ValueError('cannot revive active or empty segments')
    needed=sorted({op['segment'] for a in model['actions'] for op in a['ops'] if op['kind']=='init'})
    indices={old:new for new,old in enumerate(needed)};result=copy.deepcopy(model)
    result['segments']=[result['segments'][i] for i in needed]
    for action in result['actions']:
        ops=[]
        for op in action['ops']:
            if op['kind']=='drop' and op['segment'] not in indices:continue
            if 'segment' in op:op['segment']=indices[op['segment']]
            ops.append(op)
        action['ops']=ops
    return result,[left[i] for i in needed],[right[i] for i in needed],needed
def analyse(model,left,right):
    reduced,l,r,needed=project(model,left,right);prepared=w.prepare(reduced,l,r)
    return {'model':reduced,'prepared':prepared,'keptOriginalSegmentIndices':needed,'removedSegments':len(model['segments'])-len(needed)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',type=w.bits,required=True);p.add_argument('--right',type=w.bits,required=True);v=p.parse_args()
    try:
        r=analyse(w.g.parse(k.p.read(v.source)),v.left,v.right)
        result={'proof':r['prepared']['proof'],'keptOriginalSegmentIndices':r['keptOriginalSegmentIndices'],'removedSegments':r['removedSegments']}
    except ValueError as e:result={'status':'unsupported','reason':str(e)}
    result['sourceSha256']=hashlib.sha256(v.source.read_bytes()).hexdigest();v.out.write_text(json.dumps(result,indent=2))
