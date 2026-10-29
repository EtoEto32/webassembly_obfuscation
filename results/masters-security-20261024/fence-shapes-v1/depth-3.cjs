"use strict";
function u32(x){if(!Number.isInteger(x)||x<0||x>4294967295)throw Error("u32");}
function record(x,keys){if(!x||typeof x!=="object"||Array.isArray(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))throw Error("record shape");}
function variant(x){if(!x||typeof x!=="object"||Array.isArray(x)||typeof x.tag!=="string"||Object.keys(x).some(k=>k!=="tag"&&k!=="val"))throw Error("variant shape");}
function resource(x,permission,deps,resolve){x=resolve(x);record(x,["slot","generation"]);u32(x.slot);u32(x.generation);deps.push({slot:x.slot,generation:x.generation,permission});}
exports.project=function(value,resolve){if(typeof resolve!=="function")throw Error("host resolver required");const deps=[];
record(value,["firstFile", "nested", "batches"]);
resource(value["firstFile"],"read",deps,resolve);
if (value["nested"] !== undefined) {
variant(value["nested"]); if (value["nested"].tag === "some") {
if (!Object.hasOwn(value["nested"],"val")) throw Error("missing option payload");
if (value["nested"].val !== undefined) {
resource(value["nested"].val,"write",deps,resolve);
}
} else if (value["nested"].tag !== "none" || Object.hasOwn(value["nested"],"val")) throw Error("option shape");
}
if (!Array.isArray(value["batches"]) || value["batches"].length > 4096) throw Error("list shape/bound");
for (const x1 of value["batches"]) {
if (x1 !== undefined) {
resource(x1,"write",deps,resolve);
}
}
return deps;};
