const fs=require('fs');const bound=Number(process.argv[3]);
if(!Number.isInteger(bound)||bound<1||bound>32)throw Error('bound');
const bytes=fs.readFileSync(process.argv[2]);
const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes));
instance.exports.reset();const values=[];
for(let i=0;i<2*bound;i++)values.push(instance.exports.step(i===0?1:0)>>>0);
console.log(JSON.stringify({values,step_calls:values.length,reset_calls:1,node:process.version}));
