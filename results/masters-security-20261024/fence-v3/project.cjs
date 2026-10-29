"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps){record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value){const deps=[];
variant(value); switch (value.tag) {
case "read": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
resource(value.val,"read",deps);
break; }
case "write": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
resource(value.val,"write",deps);
break; }
case "copy": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
record(value.val,["source", "destination"]);
resource(value.val["source"],"read",deps);
resource(value.val["destination"],"write",deps);
break; }
case "batch": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
if (!Array.isArray(value.val) || value.val.length > 4096) throw Error("list shape/bound");
for (const x1 of value.val) {
resource(x1,"write",deps);
}
break; }
case "optional": {
if (!Object.hasOwn(value,"val")) throw Error("missing variant payload");
record(value.val,["primary", "backup"]);
resource(value.val["primary"],"write",deps);
if (value.val["backup"] !== null) {
resource(value.val["backup"],"write",deps);
}
break; }
case "idle": {
if (Object.hasOwn(value,"val")) throw Error("payload on empty case");
break; }
default: throw Error("unknown variant"); }
return deps;};
