import json, math, random, re, sys
from pathlib import Path
import prototype as p

def ev(coeff,x,mask):
    result=0
    for c in reversed(coeff):result=(result*x+c)&mask
    return result

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    checks=0;closures=0;precisions=[]
    for w in range(2,9):
        mask=(1<<w)-1
        for coeff in ([3,5,1<<max(1,w//2)],[17,3,0,1<<max(1,w//2)],[5,7,1<<max(1,w//2),0,1<<max(1,w-2)]):
            for full in (False,True):
                e,updates,rounds=p.closure(coeff,w,full);closures+=1
                for x in range(1<<w):
                    z={j:((1<<v)*pow(x,j))&mask for j,v in e.items()}
                    for u in range(1<<w):
                        xp=(ev(coeff,x,mask)+u)&mask
                        for j,ts in updates.items():
                            actual=sum(c*pow(u,l)*(z[k] if k else 1) for k,l,c in ts)&mask
                            expected=((1<<e[j])*pow(xp,j))&mask
                            assert actual==expected,(w,coeff,full,x,u,j)
                        checks+=1
                precisions.append({'w':w,'coeff':coeff,'full':full,'exponents':e,'rounds':rounds})
    p.q.save(out/'small-model.json',{'closures':closures,'state_input_pairs':checks,'mismatches':0,'rows':precisions})
    cases=json.loads((folder/'cases.json').read_text());attacks=json.loads((folder/'attacks.json').read_text());cert=[]
    for attack in attacks:
        assert attack['status']=='candidate_recovered'
        name=attack['file'].split('-')[0];a=cases[name];b=attack['coefficients_mod_2_31'];degree=max(len(a),len(b))-1
        values=[(ev(a,x,(1<<31)-1)-ev(b,x,(1<<31)-1))% (1<<31) for x in range(degree+1)]
        differences=[]
        while values:
            differences.append(values[0]);values=[(values[i+1]-values[i])% (1<<31) for i in range(len(values)-1)]
        assert not any(differences)
        cert.append({'file':attack['file'],'degree':degree,'newton_differences_mod_2_31':differences,'scope':'all-integer polynomial-function equality; source profile guarantees induction, not arbitrary Wasm proof'})
    rows=json.loads((folder/'manifest.json').read_text());cross=[]
    for row in rows:
        if row.get('negative'):continue
        src=folder/row['file'];m=p.q.read(src);fs=[e for e in m[1:] if e[0]=='func'];exports={e[1].strip('"'):int(e[2][1]) for e in m[1:] if e[0]=='export'}
        wrappers=[];expected=[]
        for i,s in enumerate((0,0xffffffff,0x80000000)):
            xs=[0,1,0xffffffff,0x12345678];x=s
            for u in xs:x=(ev(cases[row['name']],x,p.MASK)+u)&p.MASK
            expected.append(x*x&p.MASK)
            body='(call %d %s)'%(exports['reset'],p.c(s))
            body+=''.join('(drop (call %d %s))'%(exports['step'],p.c(u)) for u in xs)
            body+='(call %d)'%exports['peek']
            wrappers.append('(func (export "probe%d") (result i32) %s)'%(i,body))
        f=out/(src.stem+'-interp.wasm');p.q.compile(p.q.w.emit(m)[:-1]+''.join(wrappers)+')',f)
        log=p.q.w.tool('wasm-interp',[f,'--run-all-exports']);f.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[int(x) for x in re.findall(r'probe\d+\(\) => i32:(\d+)',log)];assert got==expected,(row,got,expected)
        cross.append({'file':row['file'],'expected':expected,'actual':got,'step_calls':12,'reset_calls':3,'observations':3})
    rejected=[]
    texts={'memory':p.source(cases['quadratic']).replace('(module','(module (memory 1)',1),'wrong-output':p.source(cases['quadratic']).replace('(i32.mul (global.get 0) (global.get 0))','(global.get 0)'),'non-polynomial':p.source(cases['quadratic']).replace('i32.add','i32.xor',1)}
    for name,text in texts.items():
        f=out/(name+'.wasm');p.q.compile(text,f)
        try:p.parse(f)
        except ValueError as exc:rejected.append({'name':name,'reason':str(exc)})
        else:raise AssertionError('invalid source accepted')
    p.q.save(out/'audit.json',{'closures':closures,'state_input_pairs':checks,'polynomial_certificates':cert,'wabt':cross,'wabt_step_calls':len(cross)*12,'wabt_observations':len(cross)*3,'rejected':rejected})
    print(json.dumps({'closures':closures,'state_input_pairs':checks,'certificates':len(cert),'wabt_steps':len(cross)*12,'rejected':len(rejected)}))
if __name__=='__main__':main(*sys.argv[1:])
