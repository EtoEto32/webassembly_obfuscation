// Transport bookkeeping only; this does not establish validity of a hash.
function instrumentConnection(Connection, log) {
  const receive = Connection.prototype.receive;
  Connection.prototype.receive = function(raw) {
    let message;
    try { message = JSON.parse(raw); }
    catch(error) { log('bridge-events.jsonl', {event:'response_parse_error', message:String(error)}); }
    if (message && message.method === 'job') {
      log('stratum-jobs.jsonl', {event:'job_notification', response:message,
        matched_miner:Boolean(this.minerId[message.params && message.params.id])});
      // xmrig-proxy 6.18.0 Miner::sendJob omits params.id on updates;
      // coin-hive-stratum 2.6.11 requires it to route the job. This
      // connection is dedicated to one authenticated local worker group.
      if (message.params && message.params.id === undefined) {
        const sessions = Object.keys(this.minerId);
        if (sessions.length !== 1) throw new Error('Cannot route job without one authenticated session');
        message.params.id = sessions[0];
        log('stratum-jobs.jsonl', {event:'local_session_routing', job_id:message.params.job_id});
        raw = JSON.stringify(message);
      }
    }
    const pending = message && this.rpc[message.id];
    if (pending && pending.message.method === 'submit') {
      const status = message.result && message.result.status;
      log('shares.jsonl', {event:status === 'OK' ? 'accepted' : message.error ? 'rejected' : 'response_unclassified',
        rpc_id:message.id, job_id:pending.message.params.job_id,
        nonce:pending.message.params.nonce, response:message});
    }
    return receive.call(this, raw);
  };
  const ready = Connection.prototype.ready;
  Connection.prototype.ready = function() {
    const write = this.socket.write;
    this.socket.write = function(data, ...args) {
      // A false return means backpressure, not failure to queue the write.
      const result = write.call(this, data, ...args);
      let message;
      try { message = JSON.parse(data.toString()); } catch (_) { return result; }
      if (message.method === 'submit') {
        log('shares.jsonl', {event:'submitted', stage:'local_proxy_socket_write',
          rpc_id:message.id, job_id:message.params.job_id,
          nonce:message.params.nonce, result:message.params.result});
      }
      return result;
    };
    return ready.call(this);
  };
}
module.exports = {instrumentConnection};
