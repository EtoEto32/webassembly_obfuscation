/* Parse JS as data. Never import, evaluate, or execute corpus JavaScript. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const acorn = require(path.join(root, '.tools/js-parser/node_modules/acorn'));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function extract(source) {
  let ast, mode, lastError;
  for (const sourceType of ['module', 'script']) {
    try {
      ast = acorn.parse(source, {ecmaVersion: 'latest', sourceType,
        allowReturnOutsideFunction: true, allowHashBang: true, locations: true});
      mode = sourceType; break;
    } catch (error) { lastError = error; }
  }
  if (!ast) throw lastError;
  const found = [], todo = [ast];
  while (todo.length) {
    const node = todo.pop();
    let bytes, encoding;
    if (node.type === 'ArrayExpression' && node.elements.length >= 8 &&
        node.elements.every(x => x && x.type === 'Literal' &&
          Number.isInteger(x.value) && x.value >= 0 && x.value <= 255)) {
      if ([0,97,115,109].every((x,i) => node.elements[i].value === x)) {
        bytes = Buffer.from(node.elements.map(x => x.value)); encoding = 'literal_numeric_array';
      }
    } else if (node.type === 'Literal' && typeof node.value === 'string') {
      let value = node.value.replace(/^data:[^,]*;base64,/, '');
      if (/^AGFzbQ[A-Za-z0-9+/]*={0,2}$/.test(value)) {
        const decoded = Buffer.from(value, 'base64');
        if (decoded.length >= 8 && decoded.toString('base64').replace(/=+$/, '') === value.replace(/=+$/, '')) {
          bytes = decoded; encoding = 'literal_base64_string';
        }
      }
    }
    if (bytes) found.push({bytes, encoding, start_utf16: node.start,
      end_utf16: node.end, line: node.loc.start.line, column: node.loc.start.column});
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) {
        for (const child of value) if (child && typeof child.type === 'string') todo.push(child);
      } else if (value && typeof value.type === 'string') todo.push(value);
    }
  }
  return {mode, found: found.sort((a,b) => a.start_utf16-b.start_utf16)};
}

function main() {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'experiments/archive-registry.json')));
  const selected = new Set(process.argv.slice(2));
  for (const item of registry.filter(r => r.dataset === 'wobfuscator' && (!selected.size || selected.has(r.id)))) {
    const base = path.join(root, 'data/extracted', item.id);
    const inventory = JSON.parse(fs.readFileSync(path.join(root, 'data/catalog', item.id+'-archive', 'inventory.json')));
    const receipt = JSON.parse(fs.readFileSync(path.join(root, 'data/archives', item.filename+'.receipt.json')));
    const output = path.join(root, 'data/catalog', item.id+'-js');
    fs.mkdirSync(output, {recursive:true});
    const rows = [], files = [], failures = [];
    for (const member of inventory) {
      if (member.directory || member.link || !/\.(?:js|mjs|cjs)$/i.test(member.path)) continue;
      const file = path.resolve(base, member.path);
      if (!file.startsWith(base+path.sep)) throw new Error('Path outside extraction root');
      const record = {path:member.path, dependency_path:member.path.includes('/node_modules/')};
      try {
        const raw = fs.readFileSync(file), source = raw.toString('utf8');
        record.sha256 = hash(raw); record.bytes = raw.length;
        // Parse every selected JS file, so unusual literal formatting is not
        // silently filtered out by a text search. Unsupported syntax is logged.
        const result = extract(source);
        Object.assign(record, {status:'parsed', parse_mode:result.mode, wasm_literals:result.found.length});
        for (const found of result.found) {
          const sha = hash(found.bytes), object = 'data/objects/'+sha+'.bin';
          const row = {dataset:item.dataset, artifact:item.id+'-js',
            path:member.path+'#wasm-literal-utf16-'+found.start_utf16,
            source_js_path:member.path, source_js_sha256:record.sha256,
            source_js_local:path.relative(root,file).split(path.sep).join('/'),
            js_encoding:found.encoding, js_start_utf16:found.start_utf16,
            js_end_utf16:found.end_utf16, js_line:found.line, js_column:found.column,
            dependency_path:record.dependency_path, archive_url:item.url,
            archive_sha256:receipt.sha256, bytes:found.bytes.length, sha256:sha,
            wasm_magic:true, object, acquisition_status:'stored_verified',
            hash_evidence:'computed_from_statically_decoded_js_literal',
            extraction_scope:'literal bytes only; runtime use and reachability not inferred'};
          try {
            const destination = path.join(root,object);
            if (!fs.existsSync(destination)) fs.writeFileSync(destination,found.bytes);
            if (hash(fs.readFileSync(destination)) !== sha) throw new Error('Object hash mismatch');
          } catch(error) { row.acquisition_status='local_io_failed';row.acquisition_error=error.message; }
          rows.push(row);
        }
      } catch (error) {
        record.status='read_or_parse_failed'; record.error=error.message;
        failures.push(record);
      }
      files.push(record);
    }
    fs.writeFileSync(path.join(output,'acquisition.jsonl'),rows.map(r=>JSON.stringify(r)+'\n').join(''));
    fs.writeFileSync(path.join(output,'js-coverage.jsonl'),files.map(r=>JSON.stringify(r)+'\n').join(''));
    const summary = {dataset:item.dataset,artifact:item.id+'-js',parser:'acorn '+acorn.version,
      js_files:files.length,parsed:files.filter(r=>r.status==='parsed').length,
      candidate_wasm_members:rows.length,unique_downloaded_sha256:new Set(rows.map(r=>r.sha256)).size,
      stored_verified_paths:rows.filter(r=>r.acquisition_status==='stored_verified').length,
      failures, scope:'all regular .js/.mjs/.cjs files in validated archive inventory, including dependencies; numeric and base64 literals; no evaluation or constant folding'};
    fs.writeFileSync(path.join(output,'acquisition-summary.json'),JSON.stringify(summary,null,2));
    console.log(JSON.stringify({...summary,failures:failures.length}));
  }
}
module.exports = {extract};
if (require.main === module) main();
