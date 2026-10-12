
// Preprocessor Directives and Include Guards
// This is an include guard. It prevents this header file from being included more than once, which can cause redefinition errors.
#ifndef MATH_UTILS_H
#define MATH_UTILS_H




// Included Libraries
// These are the included standard libraries. They provide various functionalities 
// like standard integer types (stdint.h), size types (stddef.h), 
// mathematical functions (math.h), standard I/O (stdio.h), and standard library functions (stdlib.h).
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>



// Type Definitions 
// Defines types for integers (INT_TYPE) and unsigned integers (UINT_TYPE) used in the library. int8_t and uint8_t are 8-bit integer types.
#define INT_TYPE int8_t 
// #define INT_TYPE int 
#define UINT_TYPE uint8_t 
// #define UINT_TYPE unsigned 


// Helper Macros
// A macro to suppress "unused variable" warnings.
#define UNUSED(x) (void)(x)

// Calculates the maximum values for UINT_TYPE and INT_TYPE using the pow function and sizeof operator.
#define MAX_UINT_TYPE    (UINT_TYPE)(pow(2,sizeof(UINT_TYPE)*8)-1)
#define MAX_INT     (INT_TYPE)(pow(2,sizeof(INT_TYPE)*7)-1)

// Utility Macros
// Macros for calculating minimum and maximum of two numbers.
#define MIN(X,Y) (((X) < (Y)) ? (X) : (Y))
#define MAX(X,Y) (((X) > (Y)) ? (X) : (Y))
// Macro to calculate the length of an array.
#define ARR_LEN(x) (sizeof(x)/sizeof(x[0]))



// Struct Definition
// Defines a Pair struct with two fields of type INT_TYPE.
typedef struct _Pair
{
    INT_TYPE a;
    INT_TYPE b;
} Pair;

// Function Declarations
// Declares a series of functions for mathematical operations like calculating the greatest common divisor (gcd), 
// extended greatest common divisor (extended_gcd), and so on. The actual implementations of 
// these functions would be in a corresponding .c file.
UINT_TYPE   gcd(UINT_TYPE m1, UINT_TYPE m2);
Pair        gcdExt(UINT_TYPE a, UINT_TYPE b); // a > b

unsigned   extended_gcd(unsigned a, unsigned b, int *x, int *y);

void        printCoPrimes(UINT_TYPE start, UINT_TYPE end, FILE* out);

int         isPrime(UINT_TYPE n);
int         printPrimes(UINT_TYPE n);

int         printFactors(unsigned n);

unsigned    iPow(unsigned base, unsigned exp);

// End of Include Guard
// End of the include guard. Closes the #ifndef at the beginning.
#endif 