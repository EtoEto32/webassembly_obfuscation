"""Independent restricted write-effect derivation from Wasm bytes and stack.

No imports of effects.py, WAT readers, or the producer's implementation.
Caller MUST validate the exact bytes with a standard Wasm validator first.
This implementation is deliberately incomplete and is not formally verified.
"""
import hashlib
import json

class Unsupported(ValueError):pass
class Reader:
    def __init__(self,data):self.data=data;self.pos=0
    def byte(self):
        if self.pos>=len(self.data):raise Unsupported('unexpected EOF')
        x=self.data[self.pos];self.pos+=1;return x
    def take(self,n):
        if n<0 or self.pos+n>len(self.data):raise Unsupported('section bound')
        r=self.data[self.pos:self.pos+n];self.pos+=n;return r
    def uint(self):
        n=0
        for i in range(5):
            x=self.byte();n|=(x&127)<<(7*i)
            if x<128:return n
        raise Unsupported('long u32 LEB')
    def sint32(self):
        n=0
        for i in range(5):
            x=self.byte();n|=(x&127)<<(7*i)
            if x<128:
                if x&64:n-=1<<(7*(i+1))
                return n&0xffffffff
        raise Unsupported('long i32 LEB')
    def name(self):return self.take(self.uint()).decode('utf8')
    def types(self):return [self.byte() for _ in range(self.uint())]

def module(data):
    r=Reader(data)
    if r.take(8)!=b'\0asm\x01\0\0\0':raise Unsupported('Core Wasm v1 required')
    types=[];function_types=[];bodies=[];imports=[];exports={};memories=[]
    while r.pos<len(data):
        section=r.byte();s=Reader(r.take(r.uint()))
        if section==1:
            for _ in range(s.uint()):
                if s.byte()!=0x60:raise Unsupported('function types only')
                types.append((s.types(),s.types()))
        elif section==2:
            for _ in range(s.uint()):
                mod,name,kind=s.name(),s.name(),s.byte()
                if kind!=0:raise Unsupported('only function imports supported')
                imports.append((mod,name,s.uint()))
        elif section==3:function_types=[s.uint() for _ in range(s.uint())]
        elif section==5:
            for _ in range(s.uint()):
                flags=s.uint()
                if flags not in (0,1):raise Unsupported('nonshared memory32 required')
                minimum=s.uint();maximum=s.uint() if flags else None;memories.append((minimum,maximum))
        elif section==7:
            for _ in range(s.uint()):
                name=s.name();kind=s.byte();idx=s.uint();exports[name]=(kind,idx)
        elif section==10:bodies=[s.take(s.uint()) for _ in range(s.uint())]
        # Validated non-code sections do not execute during this callback.
    if len(memories)!=1 or exports.get('memory')!=(2,0):raise Unsupported('one defined exported memory required')
    if len(function_types)!=len(bodies):raise Unsupported('function/code mismatch')
    return types,function_types,bodies,imports,exports

def instructions(reader):
    result=[]
    while True:
        op=reader.byte()
        if op in (0x0b,0x05):return result,op
        if op in (0x02,0x04):
            if reader.byte()!=0x40:raise Unsupported('void block types only')
            body,end=instructions(reader)
            if op==0x02:
                if end!=0x0b:raise Unsupported('else in block')
                result.append(('block',body))
            else:
                other=[]
                if end==0x05:
                    other,end=instructions(reader)
                if end!=0x0b:raise Unsupported('if end')
                result.append(('if',body,other))
        elif op in (0x00,0x01,0x0f,0x1a,0x1b,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x6a,0x6b,0x71):result.append((op,))
        elif op in (0x0c,0x0d,0x10,0x20,0x21,0x22,0x23):result.append((op,reader.uint()))
        elif op==0x41:result.append((op,reader.sint32()))
        elif op in (0x28,0x2c,0x2d,0x2e,0x2f,0x36,0x3a,0x3b):result.append((op,reader.uint(),reader.uint()))
        elif op==0xfc:
            sub=reader.uint()
            if sub==10:
                if reader.uint()!=0 or reader.uint()!=0:raise Unsupported('multi-memory copy')
                result.append(('copy',))
            elif sub==11:
                if reader.uint()!=0:raise Unsupported('multi-memory fill')
                result.append(('fill',))
            else:raise Unsupported('unsupported bulk opcode '+str(sub))
        else:raise Unsupported('unsupported opcode 0x%02x'%op)

def derive(data,entry='callback'):
    types,ftypes,bodies,imports,exports=module(data)
    if entry not in exports or exports[entry][0]!=0:raise Unsupported('missing function entry')
    entry_index=exports[entry][1]
    if entry_index<len(imports):raise Unsupported('entry must be defined')
    if types[ftypes[entry_index-len(imports)]]!=([0x7f]*3,[]):raise Unsupported('entry signature must be (i32,i32,i32)->()')
    writes=[];visited=set();fuel=[20000]
    def spend():
        fuel[0]-=1
        if fuel[0]<0:raise Unsupported('analysis budget')
    def sequence(nodes,env,operand,labels,calls):
        flows=[(None,env,operand)]
        for node in nodes:
            following=[]
            for target,local,stack in flows:
                if target is not None:following.append((target,local,stack));continue
                following+=step(node,local,stack,labels,calls)
            flows=following
            if len(flows)>256:raise Unsupported('path budget')
        return flows
    def step(node,local,stack,labels,calls):
        spend();op=node[0]
        if op==0x41:stack.append(['const',node[1]])
        elif op==0x20:stack.append(local[node[1]])
        elif op==0x21:local[node[1]]=stack.pop()
        elif op==0x22:local[node[1]]=stack[-1]
        elif op==0x23:stack.append(None)
        elif op in (0x6a,0x6b,0x71):
            b=stack.pop();a=stack.pop();stack.append(None if a is None or b is None else [{0x6a:'add',0x6b:'sub',0x71:'and'}[op],a,b])
        elif op==0x45:stack.pop();stack.append(None)
        elif isinstance(op,int) and 0x46<=op<=0x4f:stack.pop();stack.pop();stack.append(None)
        elif op in (0x28,0x2c,0x2d,0x2e,0x2f):stack.pop();stack.append(None)
        elif op in (0x36,0x3a,0x3b):
            stack.pop();address=stack.pop()
            if address is None:raise Unsupported('unknown store address')
            writes.append({'addr':address,'offset':node[2],'length':['const',{0x36:4,0x3a:1,0x3b:2}[op]]})
        elif op in ('copy','fill'):
            length=stack.pop();stack.pop();address=stack.pop()
            if address is None or length is None:raise Unsupported('unknown bulk range')
            writes.append({'addr':address,'offset':0,'length':length})
        elif op==0x1a:stack.pop()
        elif op==0x1b:
            stack.pop();b=stack.pop();a=stack.pop();stack.append(a if a==b else None)
        elif op==0x10:
            index=node[1]
            if index<len(imports):raise Unsupported('reachable host import')
            parameters,results=types[ftypes[index-len(imports)]]
            args=[stack.pop() for _ in parameters][::-1];function(index,args,calls)
        elif op in ('block','if'):
            if op=='if':stack.pop()
            height=len(stack);branches=[node[1]] if op=='block' else [node[1],node[2]]
            flows=[]
            for branch in branches:flows+=sequence(branch,local.copy(),stack.copy(),labels+[height],calls)
            return[(None if t==0 else t-1 if isinstance(t,int) else t,e,s) for t,e,s in flows]
        elif op in (0x0c,0x0d):
            if op==0x0d:stack.pop()
            depth=node[1];target_stack=stack[:labels[-1-depth]]
            branch=(depth,local.copy(),target_stack)
            return[(None,local,stack),branch] if op==0x0d else[branch]
        elif op==0x0f:return[('return',local,[])]
        elif op==0x00:return[]
        elif op!=0x01:raise Unsupported('unimplemented instruction')
        return[(None,local,stack)]
    def function(index,args,calls):
        spend()
        if index<len(imports):raise Unsupported('entry is host import')
        if index in calls:raise Unsupported('recursive call')
        parameters,results=types[ftypes[index-len(imports)]]
        if parameters!=[0x7f]*len(args) or results:raise Unsupported('i32 params and void functions only')
        reader=Reader(bodies[index-len(imports)]);local=args.copy()
        for _ in range(reader.uint()):
            count=reader.uint();kind=reader.byte()
            if kind!=0x7f or count>100000:raise Unsupported('i32 local/bounded count required')
            local += [['const',0] for _ in range(count)]
        code,end=instructions(reader)
        if end!=0x0b or reader.pos!=len(reader.data):raise Unsupported('function ending')
        visited.add(index);flows=sequence(code,local,[],[0],calls+(index,))
        if any(t not in (None,0,'return') for t,e,s in flows):raise Unsupported('unresolved function branch')
    try:
        function(exports[entry][1],[['arg',i] for i in range(3)],())
        unique=[]
        for w in writes:
            if w not in unique:unique.append(w)
        return{'kind':'ranges','writes':unique,'visitedFunctions':sorted(visited),'checker':'stack-bytes-v1'}
    except (Unsupported,IndexError,KeyError,TypeError) as e:
        return{'kind':'full','reason':str(e),'checker':'stack-bytes-v1'}

def check(data,proposal,digest,entry='callback'):
    if hashlib.sha256(data).hexdigest()!=digest:return{'accepted':False,'reason':'binary digest mismatch'}
    try:derived=derive(data,entry)
    except (Unsupported,IndexError,KeyError,TypeError) as e:return{'accepted':False,'reason':'embedding/format contract: '+str(e)}
    if proposal.get('kind')=='full':return{'accepted':True,'mode':'full-copy','derived':derived}
    if proposal.get('kind')!='ranges' or derived['kind']!='ranges':return{'accepted':False,'reason':'range derivation unsupported','derived':derived}
    def uint(x):return type(x) is int and 0<=x<=0xffffffff
    def expr(e,depth=0):
        if depth>128 or not isinstance(e,list) or not e:return False
        if e[0]=='const':return len(e)==2 and uint(e[1])
        if e[0]=='arg':return len(e)==2 and type(e[1]) is int and 0<=e[1]<3
        return len(e)==3 and e[0] in ('add','sub','and') and expr(e[1],depth+1) and expr(e[2],depth+1)
    proposed=proposal.get('writes')
    if not isinstance(proposed,list) or len(proposed)>20000:return{'accepted':False,'reason':'write list format/bound'}
    for w in proposed:
        if not isinstance(w,dict) or set(w)!=set(('addr','offset','length')) or not uint(w['offset']) or not expr(w['addr']) or not expr(w['length']):
            return{'accepted':False,'reason':'write expression format/bound'}
    # Exact syntactic effect membership is intentionally conservative. It may
    # reject equivalent/wider summaries; it cannot silently omit a derived write.
    encoded=lambda w:json.dumps(w,sort_keys=True,separators=(',',':'))
    supplied={encoded(w) for w in proposal.get('writes',[])}
    missing=[w for w in derived['writes'] if encoded(w) not in supplied]
    return{'accepted':not missing,'mode':'range-checked','missing':missing,'derived':derived}
