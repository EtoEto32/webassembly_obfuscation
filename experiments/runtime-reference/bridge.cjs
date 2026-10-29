// Reference coin-hive-stratum transport. Only talks to local xmrig-proxy.
const fs = require('fs');
const path = require('path');
const Proxy = require('coin-hive-stratum');
// Resolve beside the exact Proxy entry point: a bind mount and NODE_PATH
// can otherwise produce two copies and instrument the unused Connection.
const Connection = require(path.join(path.dirname(require.resolve('coin-hive-stratum')), 'Connection.js')).default;
const configPath = process.argv[2];
if (!configPath) throw new Error('Provide a local config file; no default external pool');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
if (!['127.0.0.1', 'localhost'].includes(config.proxyHost)) throw new Error('Bridge must connect only to local xmrig-proxy');
if (!Number.isInteger(config.proxyPort) || config.proxyPort < 1 || config.proxyPort > 65535) throw new Error('Invalid local port');
if (typeof config.address !== 'string' || !config.address.trim()) throw new Error('A user-owned connection identifier is required');
if (!config.logDirectory) throw new Error('Specify an output directory');
fs.mkdirSync(config.logDirectory, {recursive:true});
const log = (file, data) => fs.appendFileSync(path.join(config.logDirectory, file), JSON.stringify({utc:new Date().toISOString(), ...data})+'\n');
require('./bridge-instrumentation.cjs').instrumentConnection(Connection, log);
const proxy = new Proxy({host:config.proxyHost, port:config.proxyPort,
    address:config.address, pass:config.pass || 'x', ssl:false,
    dynamicPool:false, donations:[], maxMinersPerConnection:1});
for (const event of ['open','authed','job','close','error']) {
  proxy.on(event, data => {
    const publicData = {...data};
    delete publicData.login;
    log('bridge-events.jsonl', {event, data:publicData});
  });
}
proxy.listen(8892, '127.0.0.1');
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => {proxy.kill(); process.exit(0);});
