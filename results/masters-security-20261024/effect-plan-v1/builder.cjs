"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps,resolve){x=resolve(x);record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value,resolve){if(typeof resolve!=="function")throw Error("host resolver required");const deps=[];
variant(value); switch (value.tag) {
case "read": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
resource(value.val,"read",deps,resolve);
break; }
case "write": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
resource(value.val,"write",deps,resolve);
break; }
case "copy": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
record(value.val,["source", "destination"]);
resource(value.val["source"],"read",deps,resolve);
resource(value.val["destination"],"write",deps,resolve);
break; }
case "batch": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
if (!Array.isArray(value.val) || value.val.length > 4096) throw Error("list shape/bound");
for (const x1 of value.val) {
resource(x1,"write",deps,resolve);
}
break; }
case "optional": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
record(value.val,["primary", "backup"]);
resource(value.val["primary"],"write",deps,resolve);
if (value.val["backup"] !== undefined) {
resource(value.val["backup"],"write",deps,resolve);
}
break; }
case "idle": {
if (Object.hasOwn(value,"val")) throw Error("payload on empty case");
break; }
default: throw Error("unknown variant"); }
return deps;};

const validateShape=exports.project;
exports.build=function(value){
 validateShape(value,()=>({slot:0,generation:0}));
 const ops=[];switch(value.tag){
case "read": {
const r1=ops.length; ops.push({op:"read",file:value.val});
if(ops.length>8192)throw Error("effect plan bound");
break; }
case "write": {
ops.push({op:"write",file:value.val,literal:"admitted-payload\n"});
if(ops.length>8192)throw Error("effect plan bound");
break; }
case "copy": {
const r2=ops.length; ops.push({op:"read",file:value.val["source"]});
if(ops.length>8192)throw Error("effect plan bound");
ops.push({op:"write",file:value.val["destination"],from:r2});
if(ops.length>8192)throw Error("effect plan bound");
break; }
case "batch": {
for(const r3 of value.val){
ops.push({op:"write",file:r3,literal:"admitted-payload\n"});
if(ops.length>8192)throw Error("effect plan bound");
}
break; }
case "optional": {
ops.push({op:"write",file:value.val["primary"],literal:"admitted-payload\n"});
if(ops.length>8192)throw Error("effect plan bound");
if(value.val["backup"]!==undefined){ const r4=value.val["backup"];
ops.push({op:"write",file:r4,literal:"admitted-payload\n"});
if(ops.length>8192)throw Error("effect plan bound");
}
break; }
case "idle": {
break; }
 default:throw Error('unknown recipe variant');}
 return ops;
};
