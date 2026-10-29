#include "RNC.h"

int checkM(UINT_TYPE m1, UINT_TYPE m2)
{
    if((m1*m2) <= MAX_UINT_TYPE)
    {
        return 1;
    }
    else
    {
        if(gcd(m1,m2) != 1)
        {
            return 1;
        }
        else
        {
            return 0;
        }
        
    }
}

Encoded MaxEnc(UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded M;
    M.u1 = m1-1;
    M.u2 = m2-1;
#if RNC_RAND == 1
    M = addRand(M,m1,m2);
#endif

    return M;
}

Encoded OverflowShift(UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded M;
    M.u1 = m1-1;
    M.u2 = m2-1;

    Encoded Max2;
    Max2.u1 = 255 % m1;
    Max2.u2 = 255 % m2;

    M = SubEnc(M,Max2,m1,m2);
#if RNC_RAND == 1
    M = addRand(M,m1,m2);
#endif

    return M;
}

#if RNC_RAND == 1
Encoded addRand(Encoded X, UINT_TYPE m1, UINT_TYPE m2)
{
    UINT_TYPE maxR1 = (MAX_UINT_TYPE - X.u1)/m1;
    if(maxR1 != 0)
    {
        UINT_TYPE r1 = rand() % maxR1;
        X.u1 += r1*m1;
    }

    UINT_TYPE maxR2 = (MAX_UINT_TYPE - X.u2)/m2;
    if(maxR2 != 0)
    {
        UINT_TYPE r2 = rand() % maxR2;
        X.u2 += r2*m2;
    }
    return X;
}
#endif

Encoded encode(UINT_TYPE v, UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded e;
    e.u1 = v % m1;
    e.u2 = v % m2;

#if RNC_RAND == 1
    e = addRand(e,m1,m2);
#endif

    return e;
}

UINT_TYPE decode(Encoded e, UINT_TYPE m1, UINT_TYPE m2, int* v1, int* v2)
{
    unsigned M = m1*m2;
    int x,y;
    // unsigned d = extended_gcd(m1,m2,&x,&y);
    extended_gcd(m1,m2,&x,&y);
    
    // Compute mixed radix value
    int _v1 = (e.u1) % m1;
    if(v1 != NULL)
    {
        *v1 = _v1;
    }
    // int _v2 = (e.u2 - _v1)*x % m2;
    int _v2 = (e.u2 - _v1)*x;
    _v2 = _v2;
    while( _v2 < 0)
    {
        _v2 += m2;
    }
    _v2 = _v2 % m2;

    if(v2 != NULL)
    {
        *v2 = _v2;
    }

    int v = _v1 + _v2*m1;
    v = v % M;

    return v;
}

Encoded MultEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded z;
#if RNC_RAND == 0
    UNUSED(m1);
    UNUSED(m2);
    z.u1 = x.u1*y.u1;
    z.u2 = x.u2*y.u2;
#else
    z.u1 = (x.u1 % m1)*(y.u1 % m1);
    z.u2 = (x.u2 % m2)*(y.u2 % m2);

    z = addRand(z,m1,m2); 
#endif
    return z;
}

Encoded AddEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded z;

    // unsigned z_u1;
    // unsigned z_u2;
    
#if RNC_RAND == 0
    UNUSED(m1);
    UNUSED(m2);
    z.u1 = x.u1 + y.u1;
    z.u2 = x.u2 + y.u2;
    // z_u1 = x.u1 + y.u1;
    // z_u2 = x.u2 + y.u2;
#else
    z.u1 = (x.u1 % m1) + (y.u1 % m1);
    z.u2 = (x.u2 % m2) + (y.u2 % m2);
    // z_u1 = (x.u1 % m1) + (y.u1 % m1);
    // z_u2 = (x.u2 % m2) + (y.u2 % m2);

    z = addRand(z,m1,m2);
#endif

    // making m1*m2 > 510 (255+255) avoids overflow in add long enough for next check (255 < z) to work
    if(LessEnc(encode(MAX_UINT_TYPE,m1,m2),z,m1,m2))
    {
        Encoded fixOverflow = OverflowShift(m1,m2);
        z = AddEnc(z,fixOverflow,m1,m2);
    }

    return z;
}

Encoded SubEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2)
{
    Encoded z;
#if RNC_RAND == 0
    if(y.u1 <= x.u1)
    {
        z.u1 = x.u1 - y.u1;
    }
    else
    {
        z.u1 = (x.u1 + m1) - y.u1;
    }
    if(y.u2 <= x.u2)
    {
        z.u2 = (x.u2 - y.u2);
    }
    else
    {
        z.u2 = (x.u2 + m2)- y.u2;
    }
#else
    if(y.u1 <= x.u1)
    {
        z.u1 = x.u1 - y.u1;
    }
    else
    {
        z.u1 = (x.u1 + m1) - (y.u1 % m1);
    }
    if(y.u2 <= x.u2)
    {
        z.u2 = (x.u2 - y.u2);
    }
    else
    {
        z.u2 = (x.u2 + m2) - (y.u2 % m2);
    }
    z = addRand(z,m1,m2);
#endif
    return z;
}

int EqEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2)
{
    if((x.u1 % m1) != (y.u1 % m1))
    {
        return 0;
    }
    else if((x.u2 % m2) != (y.u2 % m2) )
    {
        return 0;
    }
    else
    {
        return 1;
    }
}

int LessEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2)
{
    if(EqEnc(x,y,m1,m2))
    {
        return 0;
    }

    int a,b;
    extended_gcd(m1,m2,&a,&b); // only need to compute once, rather than twice

    // --------- Compute Mixed Radix for X ---------
    int xv1 = (x.u1) % m1;
    int xv2 = (x.u2 - xv1)*a;
    while( xv2 < 0)
    {
        xv2 += m2;
    }
    xv2 = xv2 % m2;

    // --------- Compute Mixed Radix for Y ---------
    int yv1 = (y.u1) % m1;
    int yv2 = (y.u2 - yv1)*a;
    while( yv2 < 0)
    {
        yv2 += m2;
    }
    yv2 = yv2 % m2;
    

    // --------- Compare mixed radix values ---------
    if(xv2  < yv2 )
    {
        return 1;
    }
    else if (yv2  < xv2 )
    {
        return 0;
    }
    else if( xv2  == yv2 )
    {
        if(xv1 < yv1)
        {
            return 1;
        }
        else
        {
            return 0;
        }
    }
    return 1;
}

Encoded PowEncUint(Encoded base, UINT_TYPE exp, UINT_TYPE m1, UINT_TYPE m2)
{
    if( exp == 0)
    {
        return encode(1,m1,m2);
    } else 
    if (exp == 1)
    {
        return base;
    }
    else if(exp % 2 == 1)
    {
        return(MultEnc(PowEncUint(base,exp-1,m1,m2),base,m1,m2));
    }
    else
    {
        Encoded t = PowEncUint(base,exp/2,m1,m2);
        return(MultEnc(t,t,m1,m2));
    }
    
}

Encoded DivEnc(Encoded X, Encoded Y, UINT_TYPE m1, UINT_TYPE m2)
{
    const Encoded Z = encode(0,m1,m2);


    if(EqEnc(X,Y,m1,m2))
    {
        return(encode(1,m1,m2));
    }
    else if(LessEnc(X,Y,m1,m2))
    {
        return Z;
    }
    else if(EqEnc(Y,encode(1,m1,m2),m1,m2))
    {
        return X;
    }

    Encoded R = X; // Remainder 
    Encoded Q = Z; // Quotient result

    while(!LessEnc(R,Y,m1,m2))
    {
        R = SubEnc(R,Y,m1,m2);
        Q = AddEnc(Q,encode(1,m1,m2),m1,m2);
    }
  
// #if RNC_RAND == 1
//     Q = addRand(Q,m1,m2);
// #endif
  
    return Q;
}

Encoded ModEnc(Encoded X, Encoded Y, UINT_TYPE m1, UINT_TYPE m2)
{
    const Encoded Z = encode(0,m1,m2);

    if(EqEnc(X,Y,m1,m2))
    {
        return(Z);
    }

    Encoded R = X;

    while(!LessEnc(R,Y,m1,m2))
    {
        R = SubEnc(R,Y,m1,m2);
    }
// #if RNC_RAND == 1
//     R = addRand(R,m1,m2);
// #endif

    return R;
}

Encoded Div2Enc(Encoded x, UINT_TYPE n, UINT_TYPE m1, UINT_TYPE m2) 
{
    if(n == 0)
    {
        return x;
    }

    Encoded b = encode(2,m1,m2);
    Encoded y = PowEncUint(b,n,m1,m2);

    // needed to fix division
    y.u1 = y.u1 % m1;
    y.u2 = y.u2 % m2;

    return DivEnc(x,y,m1,m2);
}

Encoded XorEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2) 
{
    Encoded z = encode(0,m1,m2);
    
    if(EqEnc(x,y,m1,m2))
    {
        return z;
    }
    else if(EqEnc(y,z,m1,m2))
    {
        return x;
    }
    else if (EqEnc(x,z,m1,m2))
    {
        return y;
    }
    
    const Encoded b = encode(2,m1,m2);
    Encoded d = encode(1,m1,m2);

    Encoded zBit[8];

    for(uint8_t i = 0; i < 8; i++) 
    {
        const Encoded xBit = DivEnc(x,d,m1,m2);
        const Encoded yBit = DivEnc(y,d,m1,m2);

        zBit[i] = AddEnc(xBit,yBit,m1,m2);
        zBit[i] = ModEnc(zBit[i],b,m1,m2); 
        zBit[i] = MultEnc(d,zBit[i],m1,m2); // shift place value

        d = MultEnc(d,b,m1,m2);
        d.u1 = d.u1 % m1;
        d.u2 = d.u2 % m2;
    }

    for(uint8_t i= 0; i < 8;i++)
    {
        z = AddEnc(z,zBit[i],m1,m2);
    }
    return z;
}

Encoded     AddEncCarry(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2,int* c)
{
    Encoded ret = AddEnc(x,y,m1,m2);

    if(c != NULL)
    {
        *c = (LessEnc(ret,x,m1,m2) || LessEnc(ret,y,m1,m2) || LessEnc(encode(MAX_UINT_TYPE,m1,m2),ret,m1,m2));
    }
    return ret;
}

unsigned    OffEnc(unsigned  base, Encoded index, UINT_TYPE m1, UINT_TYPE m2)
{
    const Encoded step = encode(sizeof(Encoded),m1,m2);

    UINT_TYPE baseTerm = base % (MAX_UINT_TYPE);
    unsigned addr = base - baseTerm;

    Encoded encShift = MultEnc(step,index,m1,m2);

    Encoded baseEnc = encode(baseTerm,m1,m2);

    int carry = 0;
    Encoded encAddr =  AddEncCarry(baseEnc,encShift,m1,m2,&carry);

    addr += decode(encAddr,m1,m2,NULL,NULL);

    if(carry)
    {
        addr += iPow(2,8);
    }

    return addr;
}
