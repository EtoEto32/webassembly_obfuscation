// Local browser Worker API adapter for the unchanged worker-only npm glue.
// This is a Node experiment host, not a claim of browser portability.
'use strict';
const { Worker: NodeWorker, isMainThread, parentPort, workerData } = require('node:worker_threads');
const fs = require('node:fs');
const vm = require('node:vm');
const { fileURLToPath, pathToFileURL } = require('node:url');
const path = require('node:path');

function localPath(value) {
  return String(value).startsWith('file:') ? fileURLToPath(new URL(value)) : String(value).split('#')[0];
}
class BrowserWorker {
  static instances = [];
  constructor(filename) {
    this.listeners = new Map();
    this.node = new NodeWorker(__filename, { workerData: { script: localPath(filename) } });
    this.node.on('message', data => this.dispatch('message', { data }));
    this.node.on('error', error => this.dispatch('error', error));
    BrowserWorker.instances.push(this);
  }
  dispatch(type, value) {
    if (this['on' + type]) this['on' + type](value);
    for (const listener of this.listeners.get(type) || []) listener(value);
  }
  postMessage(value, transfer) { this.node.postMessage(value, transfer); }
  terminate() { return this.node.terminate(); }
  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener); this.listeners.set(type, listeners);
  }
  removeEventListener(type, listener) {
    this.listeners.set(type, (this.listeners.get(type) || []).filter(x => x !== listener));
  }
}
function install(location) {
  globalThis.self = globalThis;
  globalThis.location = { href: pathToFileURL(path.resolve(location)).href };
  globalThis.Worker = BrowserWorker;
  globalThis.importScripts = (...scripts) => {
    for (const script of scripts) vm.runInThisContext(fs.readFileSync(localPath(script), 'utf8'), { filename: localPath(script) });
  };
}
if (!isMainThread) {
  install(workerData.script);
  globalThis.postMessage = (value, transfer) => parentPort.postMessage(value, transfer);
  parentPort.on('message', data => globalThis.onmessage?.({ data }));
  importScripts(workerData.script);
}
module.exports = { install, BrowserWorker };
