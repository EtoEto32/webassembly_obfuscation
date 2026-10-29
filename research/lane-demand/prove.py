"""Solver check for extracted scalar expressions, not an end-to-end compiler proof."""
import argparse
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'))
import z3
import prototype as p
from run import save

def zexpr(expr,x,y):
    cache={}
    def go(e):
        key=id(e)
        if key in cache:return cache[key]
        op=e[0]
        if op=='local.get':result=(x,y)[int(e[1])]
        elif op=='i32.const':result=z3.BitVecVal(int(e[1],0),32)
        else:
            a=go(e[1]);b=go(e[2]) if len(e)>2 else None
            operations={'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.xor':lambda:a^b,'i32.shl':lambda:a<<(b&31),'i32.shr_u':lambda:z3.LShR(a,b&31),'i32.rotl':lambda:z3.RotateLeft(a,b),'i32.rotr':lambda:z3.RotateRight(a,b),'i32.eq':lambda:z3.If(a==b,z3.BitVecVal(1,32),z3.BitVecVal(0,32)),'i32.ne':lambda:z3.If(a!=b,z3.BitVecVal(1,32),z3.BitVecVal(0,32)),'i32.eqz':lambda:z3.If(a==0,z3.BitVecVal(1,32),z3.BitVecVal(0,32)),'select':lambda:z3.If(go(e[3])!=0,a,b)}
            result=operations[op]()
        cache[key]=result;return result
    return go(expr)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);m=json.loads((a.input/'manifest.json').read_text());x,y=z3.BitVecs('x y',32);records=[]
    for f in m['files']:
        if 'kind' not in f:continue
        expected=zexpr(p.expanded(a.input/(f['model']+'.source.raw.wasm')),x,y)
        actual=zexpr(p.expanded(a.input/f['path']),x,y);s=z3.Solver();s.set(timeout=5000);s.add(expected!=actual);(a.output/(f['path']+'.smt2')).write_text(s.to_smt2(),encoding='utf-8');begin=time.perf_counter();status=s.check();record=dict(path=f['path'],result=str(status),solver_ms=(time.perf_counter()-begin)*1000)
        if status==z3.sat:record['model']=str(s.model())
        if status==z3.unknown:record['reason']=s.reason_unknown()
        records.append(record)
    rp,rc=z3.BitVecs('parent child',32);s=z3.Solver();s.set(timeout=5000);s.add(((rp+(rc-rp))&3)!=(rc&3));routing=str(s.check())
    negative=z3.Solver();negative.add((x+(y&3))!=x);negative_status=negative.check();assert negative_status==z3.sat
    result=dict(z3=z3.get_version_string(),scope='Extracted scalar source versus recovered expression over all pairs of 32-bit inputs. No full SIMD binary or compiler correctness proof.',records=records,unsat=sum(r['result']=='unsat' for r in records),sat=sum(r['result']=='sat' for r in records),unknown=sum(r['result']=='unknown' for r in records),cursor_identity=routing,negative_cursor_status=str(negative_status),negative_model=str(negative.model()))
    save(a.output/'proof.json',result);print(json.dumps({k:v for k,v in result.items() if k!='records'}))
if __name__=='__main__':main()
