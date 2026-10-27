"""Independent integer implementation of binary32 add/sub/multiply, RNE."""
MASK=0xffffffff;SIGN=1<<31;INF=0x7f800000;NAN=0x7fc00000
def nan(x):return x&0x7fffffff>INF
def zero(x):return x&0x7fffffff==0
def unpack(x):
    exp=(x>>23)&255;sig=x&0x7fffff
    if exp:sig|=1<<23
    return (-sig if x&SIGN else sig),exp-150 if exp else -149
def rounded(sig,exponent):
    sign=SIGN if sig<0 else 0;sig=abs(sig)
    if not sig:return sign
    e=sig.bit_length()-1+exponent;unit=max(-149,e-23);shift=unit-exponent
    if shift>0:
        q,rem=divmod(sig,1<<shift);half=1<<(shift-1)
        q+=int(rem>half or (rem==half and q&1))
    else:q=sig<<(-shift)
    if not q:return sign
    e=q.bit_length()-1+unit
    if e>127:return sign|INF
    if e<-126:return sign|q
    shift=q.bit_length()-24;significand=q>>shift if shift>=0 else q<<(-shift)
    return sign|((e+127)<<23)|(significand&0x7fffff)
def operation(op,x,y):
    if op=='sub':y^=SIGN;op='add'
    if nan(x) or nan(y):return NAN
    xi=x&0x7fffffff==INF;yi=y&0x7fffffff==INF
    sign=(x^y)&SIGN
    if op=='mul':
        if (xi and zero(y)) or (yi and zero(x)):return NAN
        if xi or yi:return sign|INF
        if zero(x) or zero(y):return sign
        a,ea=unpack(x);b,eb=unpack(y);v=rounded(a*b,ea+eb)
        return v if v&0x7fffffff else sign
    assert op=='add'
    if xi and yi:return NAN if sign else x
    if xi:return x
    if yi:return y
    if zero(x) and zero(y):return (x&y)&SIGN
    a,ea=unpack(x);b,eb=unpack(y);ex=min(ea,eb)
    return rounded((a<<(ea-ex))+(b<<(eb-ex)),ex)
def evaluate(nodes,root,inputs):
    vals=[]
    for t in nodes:vals.append(inputs[t[1]] if t[0]=='input' else operation(t[0],vals[t[1]],vals[t[2]]))
    x=vals[root];return NAN if nan(x) else x
