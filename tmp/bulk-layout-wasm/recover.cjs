'use strict';
// Known-family parameter extractor, not a general Wasm deobfuscator.
// Inputs: directory filenames and their Wasm bytes only. No WAT source or manifest.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const tool=path.join(process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools','wabt-1.0.42/bin/wasm2wat.exe');
const dir=path.join(__dirname,'artifacts');const rows=[];
for(const file of fs.readdirSync(dir).filter(x=>x.endsWith('.wasm'))){
 const start=process.hrtime.bigint();const bytes=fs.readFileSync(path.join(dir,file));
 const text=cp.execFileSync(tool,[path.join(dir,file)],{encoding:'utf8'});
 const masks=[...text.matchAll(/i32\.const\s+(-?\d+)\s+i32\.xor/g)].map(x=>Number(x[1])>>>0);
 const distinct=[...new Set(masks)];
 rows.push({file,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),xor_immediates:distinct,occurrences:masks.length,
 candidate:distinct.length===1?{family:'address XOR constant (family assumed)',mask:distinct[0]}:null,
 elapsed_ms:Number(process.hrtime.bigint()-start)/1e6});
 fs.writeFileSync(path.join(dir,file+'.dis.wat'),text);
}
fs.writeFileSync(path.join(dir,'recovery.json'),JSON.stringify({scope:'Static constant extraction for a known family; does not prove every occurrence is an address or reconstruct source. No execution queries.',rows},null,2));
console.log(JSON.stringify(rows,null,2));
