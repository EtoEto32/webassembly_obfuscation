"""Fixed-seed generative suite with no outcome-based selection."""
import random
from prototype import c,g,op
from fixtures import sw,module,combine


def generated_fixtures():
    rng=random.Random(2026102424);rows=[]
    for serial in range(80):
        family=serial//20;n=2+serial%5;expressions=[]
        for i in range(n):
            if family==0:
                data=op('i32.xor',g(rng.randrange(2)),c(rng.randrange(256)))
                index=op('i32.xor',g(1),c(rng.randrange(256)))
            elif family==1:
                data=op('i32.xor',g(0),c(serial&15))
                index=op('i32.or',op('i32.and',g(1),c(15)),c(16*(1+i%7)))
            elif family==2:
                data=op('i32.add',g(rng.randrange(2+i)),c(rng.randrange(256)))
                index=op('i32.xor',g(rng.randrange(2+i)),c(rng.randrange(256)))
            else:
                data=op('select',g(0),g(1),op('i32.and',g(rng.randrange(2+i)),c(1<<rng.randrange(8))))
                index=op('i32.or',op('i32.and',g(1),c(rng.choice((15,31,63,127,255)))),c(rng.choice((0,16,64,128))))
            expressions.append(sw(data,index))
        result=g(2)
        for i in range(1,n):
            name=rng.choice(('i32.xor','i32.and','i32.or','i32.add','i32.sub'))
            result=op(name,result,g(2+i))
        if serial%3==0:result=op('select',result,g(2),op('i32.and',g(1),c(1)))
        result=op('i32.xor',result,g(0))
        rows.append({'name':'generated_'+str(family)+'_'+str(serial%20).zfill(2),'module':module(expressions,result),'weights':[1+rng.randrange(5) for _ in range(n)]})
    return rows
