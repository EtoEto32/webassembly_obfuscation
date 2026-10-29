const fs=require('fs'),path=require('path'),d=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(d,'cases.json'))),rows=JSON.parse(fs.readFileSync(path.join(d,'manifest.json')));
function copy(x,op){const [dst,src,len]=op;const y=x;for(let k=0;k<len;k++)x=(x&~(1<<(dst+k)))|(((y>>>(src+k))&1)<<(dst+k));return x;}
const report={positive:[],negative:[],run_calls:0,reset_calls:0,peek_calls:0,expected_traps:0,mismatches:0};
for(const row of rows){
 const bytes=fs.readFileSync(path.join(d,row.file));if(!WebAssembly.validate(bytes))throw Error('validate');const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 const ops=cases[row.name].ops,item={file:row.file,run_calls:0,reset_calls:0,peek_calls:0,expected_traps:0,mismatches:0,witness:null};let state=0;
 function peek(where){const actual=e.peek();item.peek_calls++;if(actual!==state){item.mismatches++;item.witness??={where,actual,expected:state};}}
 function run(f){let expectedTrap=false;for(let i=0;i<ops.length;i++){if((f>>>0)===i){expectedTrap=true;break;}state=copy(state,ops[i]);}let trap=false;try{e.run(f);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;}item.run_calls++;item.expected_traps+=Number(expectedTrap);if(trap!==expectedTrap){item.mismatches++;item.witness??={f,trap,expectedTrap};}peek('run '+f);}
 peek('initial');
 for(const x of [...Array.from({length:16},(_,i)=>i),0xffffffff,0x80000000])for(const f of [...Array.from({length:ops.length+1},(_,i)=>i),-1,0x80000000]){
  e.reset(x);item.reset_calls++;state=x&15;peek('reset');run(f);run(-1);run(ops.length-1);run(0);
 }
 if(row.negative){if(!item.mismatches)throw Error('negative without counterexample '+row.file);report.negative.push(item);}
 else{if(item.mismatches)throw Error(JSON.stringify(item));report.positive.push(item);for(const k of ['run_calls','reset_calls','peek_calls','expected_traps','mismatches'])report[k]+=item[k];}
}
report.total_calls=report.run_calls+report.reset_calls+report.peek_calls;console.log(JSON.stringify(report));
