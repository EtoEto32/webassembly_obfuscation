"""Exact one-call classification for the restricted terminal/returns profile."""
import argparse,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('contract',HERE/'guard-contract.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)

def outcome(model,alive,action):
    flags=list(alive)
    for op in action['ops']:
        if op['kind']=='drop':flags[op['segment']]=False;continue
        r,d,n=op['resource'],op['dst'],op['length'];size=model['resources'][r]['length']
        if d>size or n>size-d:return 'trap'
        if op['kind']=='init':
            size=len(model['segments'][op['segment']]['values']) if flags[op['segment']] else 0
            if op['src']>size or n>size-op['src']:return 'trap'
        if op['kind']=='copy':
            size=model['resources'][op['sourceResource']]['length']
            if op['src']>size or n>size-op['src']:return 'trap'
    return 'return'

def analyse(model,left,right):
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('segment state length')
        if any(v and not s['initialLive'] for v,s in zip(side,model['segments'])):raise ValueError('cannot revive segment')
    for action in model['actions']:
        if action['readonly']:continue
        if outcome(model,left,action)!=outcome(model,right,action):
            return {'status':'impossible','guard':None,'witness':{'calls':[{'name':action['name'],'args':[]}],'shortestLength':1},'contract':'returns','protocol':'terminal'}
    return {'status':'unconditional','guard':[],'witness':None,'contract':'returns','protocol':'terminal'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',required=True);p.add_argument('--right',required=True);v=p.parse_args()
    if any(x not in '01' for x in v.left+v.right):p.error('segment bits must be 0 or 1')
    try:r=analyse(c.parse(k.p.read(v.source)),[x=='1' for x in v.left],[x=='1' for x in v.right])
    except ValueError as e:r={'status':'unsupported','reason':str(e)}
    v.out.write_text(json.dumps(r,indent=2));print(r['status'])
