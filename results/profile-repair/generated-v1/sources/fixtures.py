"""Small declared test cases; not third-party applications."""
import copy
from prototype import c, g, op


def sw(a, index):
    return ['i8x16.extract_lane_u','0',['i8x16.relaxed_swizzle',['i8x16.splat',a],['i8x16.splat',index]]]


def module(expressions, result):
    return ['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],
        ['local',*(['i32']*len(expressions))],
        *[['local.set',str(i+2),e] for i,e in enumerate(expressions)],result]]


def combine(name, expressions):
    result=expressions[0]
    for e in expressions[1:]:result=op(name,result,e)
    return result


def fixtures():
    rows=[]
    def add(name, expressions, result, weights=None):
        rows.append({'name':name,'module':module(expressions,result),'weights':weights})
    index=op('i32.or',op('i32.and',g(1),c(15)),c(16))
    a=sw(g(0),copy.deepcopy(index))
    b=sw(g(0),op('i32.or',op('i32.and',g(1),c(15)),c(32)))
    add('single',[copy.deepcopy(a)],g(2))
    add('duplicate_pair',[copy.deepcopy(a),copy.deepcopy(a)],op('i32.xor',g(2),g(3)))
    add('different_indices_pair',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.xor',g(2),g(3)))
    add('pair_and',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.and',g(2),g(3)))
    add('pair_or',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.or',g(2),g(3)))
    add('pair_equal_guard',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.eq',g(2),g(3)))
    add('pair_disjoint_masks',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.xor',op('i32.and',g(2),c(1)),op('i32.and',g(3),c(2))))
    add('pair_sum_low_bit',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.and',op('i32.add',g(2),g(3)),c(1)))
    add('dead_site',[copy.deepcopy(a)],g(0))
    add('in_range',[sw(g(0),op('i32.and',g(1),c(15)))],g(2))
    add('high_bit',[sw(g(0),op('i32.or',g(1),c(128)))],g(2))
    add('unconstrained_index',[sw(g(0),g(1))],g(2))
    add('zero_data',[sw(c(0),g(1))],g(2))
    add('cancel_plus_other',[copy.deepcopy(a),copy.deepcopy(b),sw(g(1),copy.deepcopy(index))],op('i32.or',op('i32.xor',g(2),g(3)),g(4)))
    add('chain',[copy.deepcopy(a),sw(g(2),copy.deepcopy(index))],g(3))
    add('weighted_and',[copy.deepcopy(a),copy.deepcopy(b)],op('i32.and',g(2),g(3)),[9,1])
    add('weighted_triple',[copy.deepcopy(a),copy.deepcopy(b),copy.deepcopy(a)],combine('i32.xor',[g(2),g(3),g(4)]),[9,1,5])
    for n in (3,4,5,6,8,12,15,16):
        expressions=[sw(g(0),op('i32.or',op('i32.and',g(1),c(15)),c(16*(1+i%7)))) for i in range(n)]
        add('xor_'+str(n),expressions,combine('i32.xor',[g(i+2) for i in range(n)]))
    return rows
