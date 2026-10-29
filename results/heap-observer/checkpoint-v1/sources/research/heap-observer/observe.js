// The target module is unchanged. This traverses only references it supplied.
function heapSnapshot(roots, helper, metadata, limits) {
  limits=limits||{nodes:64,elements:16};
  var ids=new Map(),queue=[],records=[],cut=0;
  function atom(x) {
    if(x===null)return null;
    if(typeof x==='bigint')return {bigint:String(x)};
    if(typeof x==='number')return Number.isNaN(x)?'nan':Object.is(x,-0)?'-0':x;
    if(typeof x==='function')return {opaque:'function'};
    if(typeof x!=='object')return {opaque:typeof x};
    if(ids.has(x))return {ref:ids.get(x)};
    if(queue.length>=limits.nodes){cut++;return {cut:'node-limit'};}
    var id=queue.length;ids.set(x,id);queue.push(x);return {ref:id};
  }
  function scalar(v,kind) {
    // Canonicalize all NaN payloads. Retain signed zero and other exact bits.
    if(kind==='f32'){var b=v>>>0;return ((b&0x7f800000)===0x7f800000&&(b&0x7fffff)!==0)?{f32:'nan'}:{f32:b};}
    if(kind==='f64'){var b=BigInt.asUintN(64,v);return ((b&0x7ff0000000000000n)===0x7ff0000000000000n&&(b&0xfffffffffffffn)!==0n)?{f64:'nan'}:{f64:b.toString(16)};}
    return atom(v);
  }
  function depth(s){var n=0;while(s.supertype!==null){s=metadata.shapes.find(t=>t.index===s.supertype);if(!s)break;n++;}return n;}
  var order=metadata.shapes.slice().sort((a,b)=>depth(b)-depth(a)||a.index-b.index);
  var rootTokens=roots.map(atom);
  for(var i=0;i<queue.length;i++){
    var obj=queue[i],shape=order.find(s=>helper[s.test](obj));
    if(!shape){records.push({id:i,opaque:'unmatched-object'});continue;}
    var fields=[],rec={id:i,type:shape.index,kind:shape.kind,fields:fields};records.push(rec);
    if(shape.kind==='array'){
      var len=helper['len_'+shape.index](obj);rec.length=len;
      for(var k=0;k<Math.min(len,limits.elements);k++)fields.push(scalar(helper[shape.fields[0].getter](obj,k),shape.fields[0].kind));
      if(len>limits.elements){rec.truncated=len-limits.elements;cut++;}
    }else for(var f of shape.fields)fields.push(scalar(helper[f.getter](obj),f.kind));
  }
  return {roots:rootTokens,objects:records,truncations:cut};
}
if(typeof module!=='undefined')module.exports={heapSnapshot};
