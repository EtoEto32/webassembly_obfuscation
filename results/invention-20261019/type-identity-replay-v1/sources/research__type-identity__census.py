"""Read raw type-section counts without Binaryen's type interning."""
from pathlib import Path
def u(data,pos):
    v=0;s=0
    while True:
        b=data[pos];pos+=1;v|=(b&127)<<s;s+=7
        if not b&128:return v,pos
def census(f):
    data=Path(f).read_bytes();pos=8;body=None
    while pos<len(data):
        kind=data[pos];length,start=u(data,pos+1)
        if kind==1:body=data[start:start+length];break
        pos=start+length
    if body is None:return dict(groups=0,types=0,structs=0,bytes=0)
    total,pos=u(body,0);widths=[];structs=0
    def value(pos):
        tag=body[pos];pos+=1
        if tag in (0x63,0x64):_,pos=u(body,pos)
        return pos
    def subtype(pos):
        nonlocal structs
        tag=body[pos];pos+=1
        if tag in (0x4f,0x50):
            n,pos=u(body,pos)
            for _ in range(n):_,pos=u(body,pos)
            tag=body[pos];pos+=1
        if tag==0x5f:
            structs+=1;n,pos=u(body,pos)
            for _ in range(n):pos=value(pos)+1
        elif tag==0x60:
            for _ in range(2):
                n,pos=u(body,pos)
                for _ in range(n):pos=value(pos)
        else:raise ValueError('Unsupported type in census')
        return pos
    for _ in range(total):
        if body[pos]==0x4e:
            width,pos=u(body,pos+1)
        else:width=1
        widths.append(width)
        for _ in range(width):pos=subtype(pos)
    assert pos==len(body)
    return dict(groups=total,types=sum(widths),structs=structs,bytes=len(body),group_widths=widths)
