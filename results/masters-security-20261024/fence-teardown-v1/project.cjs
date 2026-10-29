"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps,resolve){x=resolve(x);record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value,resolve){if(typeof resolve!=="function")throw Error("host resolver required");const deps=[];
variant(value); switch (value.tag) {
case "read": {
resource(value.val,"read",deps,resolve);
break; }
case "write": {
resource(value.val,"write",deps,resolve);
break; }
case "copy": {
record(value.val,["source", "destination"]);
resource(value.val["source"],"read",deps,resolve);
resource(value.val["destination"],"write",deps,resolve);
break; }
case "batch": {
if (!Array.isArray(value.val) || value.val.length > 4096) throw Error("list shape/bound");
for (const x1 of value.val) {
resource(x1,"write",deps,resolve);
}
break; }
case "optional": {
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
