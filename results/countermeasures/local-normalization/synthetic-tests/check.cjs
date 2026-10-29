'use strict';
const fs=require('fs'),path=require('path');
const expected=JSON.parse(fs.readFileSync(path.join(__dirname,'expected.json')));
let checked=0;for(const name of ['original','normalized']){const bytes=fs.readFileSync(path.join(__dirname,name+'.wasm'));const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes),{});for(const [fn,value] of Object.entries(expected)){if(String(instance.exports[fn]())!==value)throw Error(name+': '+fn);checked++;}}
console.log(JSON.stringify({checked,modules:2,network_used:false,mining_code:false}));
