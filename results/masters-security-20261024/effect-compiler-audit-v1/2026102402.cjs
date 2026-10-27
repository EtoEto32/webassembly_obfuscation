"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps,resolve){x=resolve(x);record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value,resolve){if(typeof resolve!=="function")throw Error("host resolver required");const deps=[];
variant(value); switch (value.tag) {
case "chain": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
record(value.val,["initial", "copies", "backup"]);
resource(value.val["initial"],"read",deps,resolve);
if (!Array.isArray(value.val["copies"]) || value.val["copies"].length > 4096) throw Error("list shape/bound");
for (const x1 of value.val["copies"]) {
record(x1,["sourceFile", "targetFile"]);
resource(x1["sourceFile"],"read",deps,resolve);
resource(x1["targetFile"],"write",deps,resolve);
}
if (value.val["backup"] !== undefined) {
resource(value.val["backup"],"write",deps,resolve);
}
break; }
case "matrix": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
if (!Array.isArray(value.val) || value.val.length > 4096) throw Error("list shape/bound");
for (const x2 of value.val) {
if (!Array.isArray(x2) || x2.length > 4096) throw Error("list shape/bound");
for (const x3 of x2) {
record(x3,["sourceFile", "targetFile"]);
resource(x3["sourceFile"],"read",deps,resolve);
resource(x3["targetFile"],"write",deps,resolve);
}
}
break; }
case "optional": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
if (value.val !== undefined) {
record(value.val,["sourceFile", "targetFile"]);
resource(value.val["sourceFile"],"read",deps,resolve);
resource(value.val["targetFile"],"write",deps,resolve);
}
break; }
default: throw Error("unknown variant"); }
return deps;};

const validateShape=exports.project;
exports.build=function(value){
 validateShape(value,()=>({slot:0,generation:0}));
 const ops=[];switch(value.tag){
case "chain": {
const r1=ops.length; ops.push({op:"read",file:value.val["initial"]});
if(ops.length>8192)throw Error("effect plan bound");
for(const r2 of value.val["copies"]){
const r3=ops.length; ops.push({op:"read",file:r2["sourceFile"]});
if(ops.length>8192)throw Error("effect plan bound");
ops.push({op:"write",file:r2["targetFile"],from:r3});
if(ops.length>8192)throw Error("effect plan bound");
}
if(value.val["backup"]!==undefined){ const r4=value.val["backup"];
ops.push({op:"write",file:r4,from:r1});
if(ops.length>8192)throw Error("effect plan bound");
ops.push({op:"write",file:r4,literal:""});
if(ops.length>8192)throw Error("effect plan bound");
}
break; }
case "matrix": {
for(const r5 of value.val){
for(const r6 of r5){
const r7=ops.length; ops.push({op:"read",file:r6["sourceFile"]});
if(ops.length>8192)throw Error("effect plan bound");
ops.push({op:"write",file:r6["targetFile"],from:r7});
if(ops.length>8192)throw Error("effect plan bound");
}
}
break; }
case "optional": {
if(value.val!==undefined){ const r8=value.val;
const r9=ops.length; ops.push({op:"read",file:r8["sourceFile"]});
if(ops.length>8192)throw Error("effect plan bound");
ops.push({op:"write",file:r8["targetFile"],from:r9});
if(ops.length>8192)throw Error("effect plan bound");
}
break; }
 default:throw Error('unknown recipe variant');}
 return ops;
};
