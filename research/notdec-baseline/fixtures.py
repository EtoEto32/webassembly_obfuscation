"""Known field-layout fixtures; baseline only, not an obfuscation invention."""
import pathlib,subprocess,struct,json,random,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
out=ROOT/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
rng=random.Random(20261021);rows=[]
for n in (8,32,128):
    keys=rng.sample(range(1,1000000),n);values=[rng.randrange(1,2147483647) for _ in keys]
    for layout in ((0,4,8),(8,0,4),(4,8,0)):
        nxt,key,val=layout;name=f'list-{n}-'+''.join(str(x) for x in layout)
        data=bytearray(12*n)
        for i in range(n):
            for off,v in ((nxt,64+12*(i+1) if i+1<n else 0),(key,keys[i]),(val,values[i])):struct.pack_into('<I',data,12*i+off,v)
        escaped=''.join('\\%02x'%b for b in data)
        wat='''(module (memory 1) (data (i32.const 64) "DATA")
          (func (export "lookup") (param $key i32) (result i32) (local $p i32)
            (local.set $p (i32.const 64))
            (block $done (loop $next
              (br_if $done (i32.eqz (local.get $p)))
              (if (i32.eq (i32.load offset=KEY (local.get $p)) (local.get $key))
                (then (return (i32.load offset=VALUE (local.get $p)))))
              (local.set $p (i32.load offset=NEXT (local.get $p)))
              (br $next))) (i32.const 0)))'''.replace('DATA',escaped).replace('KEY',str(key)).replace('VALUE',str(val)).replace('NEXT',str(nxt))
        source=out/(name+'.wat');source.write_text(wat,encoding='utf-8');binary=source.with_suffix('.wasm')
        p=subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wat2wasm.exe'),str(source),'-o',str(binary)],capture_output=True,text=True,check=True)
        oracle=dict(zip(keys,values));xs=keys+[0,-1,2147483647,-2147483648]+[rng.randrange(-2147483648,2147483648) for _ in range(512)]
        tests=[[x,oracle.get(x,0)] for x in xs];tf=source.with_suffix('.tests.json');tf.write_text(json.dumps(tests),encoding='utf-8')
        script="const fs=require('fs');const m=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1])));let n=0;for(const [x,y] of JSON.parse(fs.readFileSync(process.argv[2]))){if(m.exports.lookup(x)!==y)throw Error('mismatch '+x);n++;}console.log(JSON.stringify({passed:n}));"
        p=subprocess.run(['node','-e',script,str(binary),str(tf)],capture_output=True,text=True,check=True)
        rows.append(dict(name=name,records=n,fields={'next':nxt,'key':key,'value':val},stride=12,base=64,sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),bytes=binary.stat().st_size,execution=json.loads(p.stdout)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps({'modules':len(rows),'calls':sum(r['execution']['passed'] for r in rows)}))
