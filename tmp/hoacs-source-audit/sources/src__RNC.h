#ifndef RNC_H
#define RNC_H

#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>

#include "MathUtils.h"
#include "ANSI_FORMAT.h"

#define RNC_RAND 1

typedef struct _Encoded
{
    UINT_TYPE u1;
    UINT_TYPE u2;

// #   if RNC_M_GLOBAL == 0
//     UINT_TYPE m1;
//     UINT_TYPE m2;
// #   endif
} Encoded;

#if RNC_RAND == 1
#   include <time.h>
    Encoded addRand(Encoded X, UINT_TYPE m1, UINT_TYPE m2);
#endif


int checkM(UINT_TYPE m1, UINT_TYPE m2); // validates m1, m2 pair


Encoded     encode(UINT_TYPE v, UINT_TYPE m1, UINT_TYPE m2);
UINT_TYPE   decode(Encoded v, UINT_TYPE m1, UINT_TYPE m2, int* v1, int* v2);

Encoded     MultEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2); // must have same m terms
Encoded     AddEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2); // must have same m terms, m1*m2 > 510 (255+255) for bit-wise equivalence
Encoded     SubEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);
Encoded     ModEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);

int         EqEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);
int         LessEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);

// TODO implement bit-shift funtions
// Encoded     ShiftLeftEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);
// Encoded     ShiftRightEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2);

Encoded     PowEncUint(Encoded base, UINT_TYPE exp, UINT_TYPE m1, UINT_TYPE m2);

Encoded     DivEnc(Encoded X, Encoded Y, UINT_TYPE m1, UINT_TYPE m2);
Encoded     Div2Enc(Encoded x, UINT_TYPE n, UINT_TYPE m1, UINT_TYPE m2); // Divides by power of 2; must have same m terms
Encoded     XorEnc(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2); // must have same m terms

Encoded     AddEncCarry(Encoded x, Encoded y, UINT_TYPE m1, UINT_TYPE m2,int* c);
unsigned    OffEnc(unsigned base, Encoded index, UINT_TYPE m1, UINT_TYPE m2);
#endif