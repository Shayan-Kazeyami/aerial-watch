/** Dependency-free, video-only WebM muxer. Returns Uint8Array, not Blob.
 * chunks: EncodedVideoChunk objects, or {type:'key'|'delta',timestamp,duration?,data:Uint8Array}.
 * Timestamps/durations are integer microseconds; durationMs is the total timeline
 * duration (including any initial gap). codec is 'vp8' or 'vp9'. expectedFrames (alias expectedFrameCount)
 * is optional. Input payload + output allocations are bounded by maxOutputBytes
 * each; callers retain ownership of input buffers and must not mutate during mux.
 */
export function muxWebM({ chunks, width, height, frameRate, durationMs, codec = 'vp8', expectedFrames, expectedFrameCount = expectedFrames,
  maxOutputBytes = 128 * 1024 * 1024 } = {}) {
  const integer = (v, min, max, name) => { if (!Number.isSafeInteger(v) || v < min || v > max) throw new RangeError(`Invalid ${name}`); };
  integer(width, 1, 16384, 'width'); integer(height, 1, 16384, 'height');
  if (!Number.isFinite(frameRate) || frameRate < 0.001 || frameRate > 1000) throw new RangeError('Invalid frameRate');
  if (!Number.isFinite(durationMs) || durationMs <= 0 || durationMs > 86400000) throw new RangeError('Invalid durationMs');
  integer(maxOutputBytes, 1024, 128 * 1024 * 1024, 'maxOutputBytes');
  if (!Array.isArray(chunks) || chunks.length === 0 || chunks.length > 200000) throw new RangeError('Expected 1..200000 chunks');
  if (expectedFrameCount !== undefined) { integer(expectedFrameCount, 1, 200000, 'expectedFrameCount'); if (expectedFrameCount !== chunks.length) throw new RangeError('Frame count mismatch'); }
  if (codec !== 'vp8' && codec !== 'vp9') throw new TypeError('codec must be vp8 or vp9');
  const id = n => { const out = []; do { out.unshift(n % 256); n = Math.floor(n / 256); } while (n); return new Uint8Array(out); };
  const size = n => { let len = 1; while (n >= 2 ** (7 * len) - 1) len++; const out = new Uint8Array(len); let v = n; for (let i = len - 1; i >= 0; i--) { out[i] = v % 256; v = Math.floor(v / 256); } out[0] |= 1 << (8 - len); return out; };
  const bytes = v => v instanceof Uint8Array ? v : new TextEncoder().encode(v);
  const uint = n => id(n);
  const el = (tag, payload) => { const parts = Array.isArray(payload) ? payload : [payload]; const body = parts.reduce((s, p) => s + (p.length ?? p.byteLength), 0); const head = [id(tag), size(body)]; return { parts: [...head, ...parts], length: head[0].length + head[1].length + body }; };
  const u = (tag, n) => el(tag, uint(n));
  const f64 = n => { const b = new Uint8Array(8); new DataView(b.buffer).setFloat64(0, n, false); return b; };
  const header = el(0x1a45dfa3, [u(0x4286, 1), u(0x42f7, 1), u(0x42f2, 4), u(0x42f3, 8), el(0x4282, bytes('webm')), u(0x4287, 4), u(0x4285, 2)]);
  const info = el(0x1549a966, [u(0x2ad7b1, 1000000), el(0x4489, f64(durationMs)), el(0x4d80, bytes('Assembly WebM')), el(0x5741, bytes('Assembly WebM'))]);
  const tracks = el(0x1654ae6b, [el(0xae, [u(0xd7, 1), u(0x73c5, 1), u(0x83, 1), u(0x9c, 0), el(0x86, bytes(codec === 'vp8' ? 'V_VP8' : 'V_VP9')), u(0x23e383, Math.round(1e9 / frameRate)), el(0xe0, [u(0xb0, width), u(0xba, height)])])]);
  // Validate all input before copying native chunks. At most one payload-sized copy
  // per native chunk; EBML nodes reference payloads until the single final allocation.
  let payloadBytes = 0, previous = -1;
  for (let i = 0; i < chunks.length; i++) {
    const c = chunks[i];
    if (!c || (c.type !== 'key' && c.type !== 'delta')) throw new TypeError('Invalid chunk type');
    if (i === 0 && c.type !== 'key') throw new Error('First chunk must be a keyframe');
    integer(c.timestamp, 0, Number.MAX_SAFE_INTEGER, 'timestamp');
    if (c.timestamp <= previous) throw new RangeError('Timestamps must be strictly increasing');
    if (c.timestamp / 1000 >= durationMs) throw new RangeError('Chunk starts outside duration');
    if (c.duration != null) {
      integer(c.duration, 1, Number.MAX_SAFE_INTEGER, 'chunk duration');
      if ((c.timestamp + c.duration) / 1000 > durationMs + 1) throw new RangeError('Chunk ends outside duration');
    }
    previous = c.timestamp;
    const n = c.data instanceof Uint8Array ? c.data.byteLength : c.byteLength;
    integer(n, 1, maxOutputBytes, 'chunk byteLength');
    if (!(c.data instanceof Uint8Array) && typeof c.copyTo !== 'function') throw new TypeError('Chunk needs Uint8Array data or copyTo');
    payloadBytes += n;
    if (payloadBytes + chunks.length * 16 > maxOutputBytes) throw new RangeError('Output exceeds memory/output cap');
  }
  const clusters = [], cueEntries = [];
  let current = null, clusterOffset = info.length + tracks.length;
  const finish = () => { if (current) { const node = el(0x1f43b675, current.parts); clusters.push(node); clusterOffset += node.length; } };
  for (const c of chunks) {
    const t = Math.round(c.timestamp / 1000);
    // Keyframes begin clusters for simple, reliable cue seeking. Long GOPs split
    // before signed int16 block-relative timestamps could overflow.
    if (!current || c.type === 'key' || t - current.time > 32767) {
      finish(); current = { time: t, parts: [u(0xe7, t)] };
      if (c.type === 'key') cueEntries.push(el(0xbb, [u(0xb3, t), el(0xb7, [u(0xf7, 1), u(0xf1, clusterOffset)])]));
    }
    let data = c.data;
    if (!(data instanceof Uint8Array)) { data = new Uint8Array(c.byteLength); c.copyTo(data); }
    const blockHeader = new Uint8Array(4); blockHeader[0] = 0x81;
    new DataView(blockHeader.buffer).setInt16(1, t - current.time, false); blockHeader[3] = c.type === 'key' ? 0x80 : 0;
    current.parts.push(el(0xa3, [blockHeader, data]));
  }
  finish();
  const cues = el(0x1c53bb6b, cueEntries);
  const segment = el(0x18538067, [info, tracks, ...clusters, cues]);
  const total = header.length + segment.length;
  if (total > maxOutputBytes) throw new RangeError('Output exceeds memory/output cap');
  const output = new Uint8Array(total); let offset = 0;
  const write = node => { if (node instanceof Uint8Array) { output.set(node, offset); offset += node.length; } else for (const part of node.parts) write(part); };
  write(header); write(segment); return output;
}
