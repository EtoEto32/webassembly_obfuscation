import fs from 'node:fs';
import {spawnSync} from 'node:child_process';

export function admit(checker,library,policy,consumer,allowedImports=null) {
  // Copy once and keep these exact bytes until instantiation. Passing snapshots
  // on stdin avoids validating one filesystem version and running another.
  const lib=Buffer.from(library),client=Buffer.from(consumer);
  const r=spawnSync(checker,['--stdin'],{input:JSON.stringify({library:[...lib],consumer:[...client],policy}),encoding:'utf8',timeout:60000});
  if(r.error)throw r.error;
  if(r.status!==0)return {status:'validation-error',detail:r.stderr};
  const analysis=JSON.parse(r.stdout),decision=analysis.results.find(x=>x.mode==='closure');
  if(!decision.accepted)return {status:'policy-reject',violations:decision.violations};
  const clientModule=new WebAssembly.Module(client);
  if(allowedImports!==null && WebAssembly.Module.imports(clientModule).some(x=>x.module!=='lib'||!allowedImports.includes(x.name)))
    return {status:'import-reject'};
  const libraryInstance=new WebAssembly.Instance(new WebAssembly.Module(lib));
  const permitted=allowedImports===null?libraryInstance.exports:Object.fromEntries(allowedImports.map(k=>[k,libraryInstance.exports[k]]));
  const clientInstance=new WebAssembly.Instance(clientModule,{lib:permitted});
  return {status:'accepted',library:libraryInstance,client:clientInstance};
}

if(process.argv[1]?.endsWith('loader.mjs')) {
  const [checker,specPath,policyPath]=process.argv.slice(2);
  const spec=JSON.parse(fs.readFileSync(specPath,'utf8')),policy=JSON.parse(fs.readFileSync(policyPath,'utf8')),rows=[];
  for(const c of spec.cases) {
    const admitted=admit(checker,fs.readFileSync(c.library),policy,fs.readFileSync(c.consumer));
    let result=null;
    if(admitted.status==='accepted') {
      try{result={type:'return',value:admitted.client.exports.run()}}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;result={type:'trap'}}
    }
    rows.push({name:c.name,secret:c.secret,status:admitted.status,result});
  }
  console.log(JSON.stringify({rows,accepted:rows.filter(x=>x.status==='accepted').length,rejected:rows.filter(x=>x.status==='policy-reject').length}));
}
