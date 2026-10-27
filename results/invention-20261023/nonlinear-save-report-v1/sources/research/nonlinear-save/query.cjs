const fs=require('fs'),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
let k=0,calls=0;function run(f){calls++;try{e.run(f);return false;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return true;}}
for(;k<=8;k++){e.reset(0);calls++;if(!run(k))break;}if(k>8)throw Error('copy profile bound');
const tables=[];for(let f=0;f<=k;f++){const row=[];for(let x=0;x<16;x++){e.reset(x);calls++;const trap=run(f);if(trap!==(f<k))throw Error('unexpected trap');row.push(e.peek());calls++;}tables.push(row);}
console.log(JSON.stringify({tables,calls}));
