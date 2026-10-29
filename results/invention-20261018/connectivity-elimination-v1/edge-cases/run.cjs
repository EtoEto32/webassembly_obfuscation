const fs=require('fs');
(async()=>{let count=0; for(const j of JSON.parse(fs.readFileSync(process.argv[2]))){
const e=(await WebAssembly.instantiate(fs.readFileSync(j.file))).instance.exports;
for(let i=0;i<j.values.length;i++){if((e.run(j.values[i])>>>0)!==j.expected[i])throw Error(j.file);count++;}}
console.log(JSON.stringify({calls:count,mismatches:0}));})().catch(e=>{console.error(e);process.exitCode=1;});
