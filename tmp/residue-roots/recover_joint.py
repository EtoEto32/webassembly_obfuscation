import pathlib,json,time,collections,itertools
ROOT=pathlib.Path(__file__).resolve().parent
class Budget(Exception):pass
def recover(coefficients,residue,width=32,limit=20000):
    s,p,q=coefficients;mask=(1<<width)-1;count=0
    def search(x,y,bits):
        nonlocal count
        count+=1
        if count>limit:raise Budget()
        z=(s-x-y)&mask
        # With x,y,z congruent mod4 and fixed sum, future high-bit choices
        # cannot affect e2/e3 below min(width,bits+2).
        observed_mask=(1<<min(width,bits+2))-1
        if ((x*y+x*z+y*z-p)&observed_mask) or ((x*y*z-q)&observed_mask):return None
        if bits==width:return [x,y,z]
        for dx,dy in [(0,0),(0,1),(1,0),(1,1)]:
            result=search(x+(dx<<bits),y+(dy<<bits),bits+1)
            if result is not None:return result
        return None
    started=time.perf_counter()
    try:
        result=search(residue,residue,2) if s%4==(3*residue)%4 else None
        status='compatible_multiset' if result is not None else 'no_factorization'
    except Budget:result=None;status='budget_exhausted'
    if result is not None:
        x,y,z=result
        assert [(x+y+z)&mask,(x*y+x*z+y*z)&mask]==[s,p]
        assert (x*y*z)&mask==q and all(v%4==residue for v in result)
    return {'status':status,'values':result,'visited_nodes':min(count,limit),'seconds':time.perf_counter()-started}

if __name__=='__main__':
    # Exhaustively validate pruning on every possible same-residue 4-bit tuple.
    small=0
    for r in range(4):
        for x,y,z in itertools.product(range(r,16,4),repeat=3):
            result=recover([(x+y+z)&15,(x*y+x*z+y*z)&15,(x*y*z)&15],r,4)
            assert result['status']=='compatible_multiset';small+=1
    rows=json.loads((ROOT/'coefficient-observations.json').read_text());out=[]
    for row in rows:
        out.append({**row,**recover(row['coefficients'],row['residue'])})
        (ROOT/'joint-recovery.json').write_text(json.dumps(out))
    summary={'groups':len(out),'small_width_complete_cases':small,'status_counts':dict(collections.Counter(r['status'] for r in out)),'maximum_seconds':max(r['seconds'] for r in out),'total_nodes':sum(r['visited_nodes'] for r in out)}
    (ROOT/'joint-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
