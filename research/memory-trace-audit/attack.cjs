'use strict';

// No fixture identity, original program, allocator log, or generation map.
// This observer hypothesis is deliberately explicit, not a general shape
// inference algorithm: nodes occupy distinct aligned granularity-byte blocks.
function recover(events, granularity = 16) {
  const sequence = [];
  const valueEdges = new Set();
  const successful = events.filter(e => e.kind === 'after');
  for (const e of successful) {
    const p = Math.floor(e.address / granularity) * granularity;
    if (sequence.length === 0 || sequence[sequence.length - 1] !== p) sequence.push(p);
  }
  const bases = new Set(sequence);
  const edges = new Set();
  for (let i = 1; i < sequence.length; i++) edges.add(`${sequence[i - 1]}:${sequence[i]}`);
  for (const e of successful) {
    const p = Math.floor(e.address / granularity) * granularity;
    if (bases.has(e.value >>> 0)) valueEdges.add(`${p}:${e.value >>> 0}`);
  }
  return {sequence, edges: [...edges].sort(), valueEdges: [...valueEdges].sort(),
    granularity, loads: successful.length,
    limitations: ['Requires aligned disjoint node blocks and multiple visits.',
      'Cannot distinguish immediate self-edges from multiple accesses within one node.',
      'Does not recover unvisited/null edges, payload expressions, or general source types.']};
}

module.exports = {recover};
