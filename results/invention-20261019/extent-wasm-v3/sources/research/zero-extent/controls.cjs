const fs=require('fs'),path=require('path');const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
function execute(file,args,pages){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,file)))).exports;e.memory.grow(pages);
 const memory=new Uint8Array(e.memory.buffer);memory.fill(0x5a);let trap=false,value;
 try{value=e.run(...args)}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true}return {trap,value,memory};}
const rows=[];for(const c of m.cases){const a=execute(c.good,c.args,c.pages),b=execute(c.bad,c.args,c.pages),diff=[];
 for(let i=0;i<a.memory.length;i++)if(a.memory[i]!==b.memory[i])diff.push({address:i,good:a.memory[i],bad:b.memory[i]});
 if(a.trap===b.trap&&a.value===b.value&&!diff.length)throw Error('Negative control missed '+c.name);
 rows.push({name:c.name,good_trap:a.trap,bad_trap:b.trap,memory_difference:diff});}
let count=0;for(const pages of [0,1,2])for(const p of [0,1,2,3,16,65535,0xffffffff]){
 const a=execute(m.normalizer.before,[p,0,0,0x12345678,0],pages),b=execute(m.normalizer.after,[p,0,0,0x12345678,0],pages);
 if(a.trap!==b.trap||a.value!==b.value||Buffer.compare(Buffer.from(a.memory),Buffer.from(b.memory)))throw Error('Normalizer operand order');count++;}
console.log(JSON.stringify({negative_controls:rows,normalizer_cases:count,normalizer_mismatches:0,rejections:m.rejections}));
