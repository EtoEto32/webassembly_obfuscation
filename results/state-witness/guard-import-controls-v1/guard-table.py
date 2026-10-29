"""Constant bulk memory/table guard synthesis. Reuses the frozen equality lattice."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('memory_guard',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
BASE=1<<32
def cell(resource,index):return resource*BASE+index
def reference(index):return index+257 # null index -1 becomes 256, disjoint from bytes

def parse(module):
    _,meta=k.augment(module,True)
    if k.p.section(module,'global'):raise g.Unsupported('globals excluded')
    resources={};memories=k.p.section(module,'memory');tables=k.p.section(module,'table')
    if memories:resources[0]={'kind':'memory','length':int(memories[0][1])*65536}
    for t,table in enumerate(tables):resources[t+1]={'kind':'table','index':t,'length':int(table[1])}
    segments=[];segindex={}
    for desc in meta['segments']:
        kind,index=desc['kind'],desc['index'];s=k.p.section(module,kind)[index]
        if kind=='data':values=list(b''.join(g.literal(x) for x in s[1:] if isinstance(x,str) and x.startswith('"')))
        else:
            start=s.index('func');values=[reference(int(x)) for x in s[start+1:]]
        segindex[(kind,index)]=len(segments);segments.append({**desc,'values':values})
    funcs=k.p.section(module,'func');types=k.p.section(module,'type');actions=[];cells=set()
    def iconst(x):
        if not isinstance(x,list) or len(x)!=2 or x[0]!='i32.const':raise g.Unsupported('nonconstant integer operand')
        return int(x[1],0)&0xffffffff
    for e in k.p.section(module,'export'):
        if e[2][0]!='func':continue
        f=funcs[int(e[2][1])];typ=types[int(next(x[1] for x in f[1:] if x[0]=='type'))][1]
        body=[x for x in f[1:] if x[0] not in k.p.DECL];name=json.loads(e[1])
        readonly=(typ==['func',['param','i32'],['result','i32']] and body==[['i32.load8_u',['local.get','0']]])
        readonly|=(len(body)==1 and len(body[0])==2 and body[0][0] in [t+'.const' for t in k.p.NUM]
                   and typ==['func',['result',body[0][0].split('.')[0]]])
        if readonly:actions.append({'name':name,'readonly':True,'ops':[]});continue
        if typ!=['func']:raise g.Unsupported('API signature/body outside profile')
        ops=[]
        for n in body:
            op=n[0]
            if op=='nop':continue
            if op in ('data.drop','elem.drop'):ops.append({'kind':'drop','segment':segindex[(op.split('.')[0],int(n[1]))]});continue
            if op not in ('memory.init','memory.copy','memory.fill','table.init','table.copy','table.fill'):raise g.Unsupported('unsupported opcode '+op)
            kind,verb=op.split('.');args=[x for x in n[1:] if isinstance(x,list)];imm=[int(x) for x in n[1:] if isinstance(x,str)]
            if len(args)!=3:raise g.Unsupported('bulk operand count')
            dst,length=iconst(args[0]),iconst(args[2])
            if length>128:raise g.Unsupported('transfer length exceeds 128')
            resource=0 if kind=='memory' else 1+(imm[0] if (verb=='init' and len(imm)==2) or verb in ('copy','fill') and imm else 0)
            item={'kind':verb,'resource':resource,'dst':dst,'length':length}
            if verb=='init':item.update({'src':iconst(args[1]),'segment':segindex[('data' if kind=='memory' else 'elem',imm[-1])]})
            elif verb=='copy':item.update({'src':iconst(args[1]),'sourceResource':0 if kind=='memory' else 1+(imm[1] if len(imm)==2 else 0)})
            elif kind=='memory':item['value']=iconst(args[1])&255
            else:
                arg=args[1]
                if arg==['ref.null','func']:item['value']=reference(-1)
                elif len(arg)==2 and arg[0]=='ref.func':item['value']=reference(int(arg[1]))
                else:raise g.Unsupported('nonconstant table.fill reference')
            if dst+length<=resources[resource]['length']:cells.update(cell(resource,i) for i in range(dst,dst+length))
            if verb=='copy' and item['src']+length<=resources[item['sourceResource']]['length']:
                cells.update(cell(item['sourceResource'],i) for i in range(item['src'],item['src']+length))
            ops.append(item)
        actions.append({'name':name,'readonly':False,'ops':ops})
    if len(cells)>256:raise g.Unsupported('footprint exceeds 256 cells')
    return {'resources':resources,'segments':segments,'actions':actions,'cells':sorted(cells),'functions':len(funcs)}

def effect(model,alive,action):
    flags=list(alive);mapping={};outcome='return'
    for op in action['ops']:
        if op['kind']=='drop':flags[op['segment']]=False;continue
        r,d,n=op['resource'],op['dst'],op['length']
        if d+n>model['resources'][r]['length']:outcome='trap';break
        if op['kind']=='init':
            data=model['segments'][op['segment']]['values'] if flags[op['segment']] else []
            if op['src']+n>len(data):outcome='trap';break
            values=[g.C(v) for v in data[op['src']:op['src']+n]]
        elif op['kind']=='copy':
            src=op['src'];sr=op['sourceResource']
            if src+n>model['resources'][sr]['length']:outcome='trap';break
            values=[mapping.get(cell(sr,i),g.M(cell(sr,i))) for i in range(src,src+n)]
        else:values=[g.C(op['value'])]*n
        for i,v in enumerate(values):mapping[cell(r,d+i)]=v
    return {'alive':tuple(flags),'mapping':mapping,'outcome':outcome}

def solve(model,left,right):
    if len(left)!=len(model['segments']) or len(right)!=len(model['segments']):raise g.Unsupported('segment state length')
    for side in (left,right):
        if any(live and not s['initialLive'] for live,s in zip(side,model['segments'])):raise g.Unsupported('cannot revive active or empty segments')
    initial=(tuple(left),tuple(right));states=[initial];index={initial:0};edges=[]
    for pair in states:
        if len(states)>1024:raise g.Unsupported('segment-state-pair bound')
        row=[]
        if pair[0]!=pair[1]:
            for action in model['actions']:
                if action['readonly']:continue
                a,b=effect(model,pair[0],action),effect(model,pair[1],action);target=(a['alive'],b['alive'])
                if target not in index:index[target]=len(states);states.append(target)
                touched=set(a['mapping'])|set(b['mapping'])
                local=g.canonical([(a['mapping'].get(i,g.M(i)),b['mapping'].get(i,g.M(i))) for i in touched]) if a['outcome']==b['outcome'] else None
                row.append({'action':action['name'],'target':index[target],'local':local,'mapping':a['mapping'],'outcomes':[a['outcome'],b['outcome']]})
        edges.append(row)
    guards=[frozenset() for _ in states]
    for iteration in range(1,1025):
        new=[g.combine(*[g.combine(e['local'],g.pullback(guards[e['target']],e['mapping'])) for e in row]) for row in edges]
        if new==guards:break
        guards=new
    else:raise g.Unsupported('fixed-point iteration bound')
    serial=lambda guard:None if guard is None else [[list(a),list(b)] for a,b in sorted(guard)]
    return {'status':'conditional' if guards[0] else ('impossible' if guards[0] is None else 'unconditional'),
      'guard':serial(guards[0]),'iterations':iteration,'states':[{'left':list(a),'right':list(b),'guard':serial(v)} for (a,b),v in zip(states,guards)],
      'cells':model['cells'],'resources':model['resources'],'functions':model['functions']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',required=True);p.add_argument('--right',required=True);v=p.parse_args()
    try:r=solve(parse(k.p.read(v.source)),[x=='1' for x in v.left],[x=='1' for x in v.right])
    except ValueError as e:r={'status':'unsupported','reason':str(e)}
    r['sourceSha256']=hashlib.sha256(v.source.read_bytes()).hexdigest();v.out.write_text(json.dumps(r,indent=2));print(r['status'])
