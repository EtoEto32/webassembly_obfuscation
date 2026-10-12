#include "MathUtils.h"

UINT_TYPE gcd(UINT_TYPE m1, UINT_TYPE m2)
{
    if(m1 == 0)
    {
        return m2;
    }
    else if(m1 == m2) // gcd(x,x) = x
    {
        return m2;
    }
    else if(m1 > m2) // flip args
    {
        return gcd(m2,m1);
    }
    else if(m1 > 0 && m2 > 0)
    {
        return gcd(m2 % m1,m1);
    }
    else
    {
        return 0; // Error, Arguments out of range
    }
    
}

// code is originally from https://www.techiedelight.com/extended-euclidean-algorithm-implementation/#
// Recursive function to demonstrate the extended Euclidean algorithm.
// It uses pointers to return multiple values.
unsigned extended_gcd(unsigned a, unsigned b, int *x, int *y)
{
    if (a == 0)
    {
        *x = 0;
        *y = 1;
        return b;
    }
 
    int _x, _y;
    unsigned gcd = extended_gcd(b % a, a, &_x, &_y);
 
    *x = _y - (b/a) * _x;
    *y = _x;
 
    return gcd;
}

Pair gcdExt(UINT_TYPE b, UINT_TYPE a) // FIXME Does not work for Coprime values (a % b != 0)
{
    if(a >= b)
    {
        Pair p;

        // Initial values
        const unsigned    r_0 = a;
        const int         s_0 = 1;
        const int         t_0 = 0;

        const unsigned    r_1 = b;
        const int         s_1 = 1;
        const int         t_1 = 0;

        // Prepare for inductive step
        unsigned    k   = 1;

        unsigned    r_ks1 = r_0;
        unsigned    s_ks1 = s_0;
        unsigned    t_ks1 = t_0;

        unsigned    r_k = r_1;
        unsigned    s_k = s_1;
        unsigned    t_k = t_1;


        p.a = s_k;
        p.b = t_k;

        unsigned    r_kp1;
        unsigned    s_kp1;
        unsigned    t_kp1;
        while (r_k > 0)
        {
            // if(r_k == 0)
            // {
            //     p.a = s_ks1;
            //     p.b = t_ks1;
            //     return p;
            // }

            unsigned    q_k = r_ks1/r_k;

            r_kp1 = r_ks1 - q_k*r_k;
            s_kp1 = s_ks1 - q_k*s_k;
            t_kp1 = t_ks1 - q_k*t_k;

            // iterate k
            k++;
            if(r_kp1 == 0)
            {
                p.a = s_k;
                p.b = t_k;
                return p;
            }

            r_ks1 = r_k;
            s_ks1 = s_k;
            t_ks1 = t_k;

            r_k = r_kp1;
            s_k = s_kp1;
            t_k = t_kp1;


        }
        

        return p;
    }
    else // Args out of Range
    {
        Pair p = gcdExt(a,b);
        return p;
    }

}

void printCoPrimes(UINT_TYPE start, UINT_TYPE end, FILE* out)
{
    // TODO check/optimize bounds of search??
    for(unsigned m = start; m < end; m++)
    {
        for(unsigned n = m; n < end; n++)
        {
            unsigned d = gcd(m,n);
            if(d == 1)
            {
                fprintf(out,"%u, %u\n",m,n);
            }
        }
    }
}

int isPrime(UINT_TYPE n)
{
    if(n == 0)
    {
        return 0;
    }
    else if (n == 1)
    {
        return 1;
    }

    for(UINT_TYPE i = 2; i <= floor(n/2); i++)
    {
        if(n % i == 0)
        {
            return 0;
        }
    }
    
    return 1;
}

int printPrimes(UINT_TYPE n)
{
    UINT_TYPE primeCount = 0;
    for(UINT_TYPE i = 1; i <= n; i++)
    {
        if(isPrime(i))
        {
            primeCount++;
            printf("%u, ",i);
        }
    }
    //putc('\n',stdout);
    printf("\n");
    return 0;
}

int printFactors(unsigned n)
{
    if(n == 0)
    {
        return 0;
    }

    printf("%u: ",n);
    for(unsigned i = 1; i <= n; i++)
    {
        if(n % i == 0)
        {
            printf("%u, ",i);
        }
    }
    //fputs("\n",stdout);
    printf("\n");
    return 0;
}

unsigned iPow(unsigned base, unsigned exp)
{
    if( exp == 0)
    {
        return 1;
    }
    else if (exp == 1)
    {
        return base;
    }
    else if(exp % 2 == 1)
    {
        return(iPow(base,exp-1)*base);
    }
    else
    {
        unsigned t = iPow(base,exp/2);
        return(t*t);
    }
    
}
