// Fixes a Piper voice config for the Windows release 2023.11.14-2, which fails on current voice JSONs
// with "aɪ is not a single codepoint". The fix: drop the multi-codepoint keys from `phoneme_id_map`.
//
// usage: node fix-piper-voice.mjs <voice.onnx.json> [more.onnx.json ...]
// The original is saved next to it as <file>.bak (once). Safe to run twice.
import { readFileSync, writeFileSync, existsSync, copyFileSync } from 'node:fs';

const files = process.argv.slice(2);
if (!files.length) { console.error('usage: node fix-piper-voice.mjs <voice.onnx.json> ...'); process.exit(2); }
for (const f of files) {
  const raw = readFileSync(f, 'utf8').replace(/^﻿/, '');
  const j = JSON.parse(raw);
  const map = j.phoneme_id_map ?? {};
  const bad = Object.keys(map).filter((k) => [...k].length > 1);
  if (!bad.length) { console.log(`${f}: nothing to fix`); continue; }
  if (!existsSync(f + '.bak')) copyFileSync(f, f + '.bak');
  for (const k of bad) delete map[k];
  writeFileSync(f, JSON.stringify(j));
  console.log(`${f}: removed ${bad.length} multi-codepoint keys (${bad.join(' ')})`);
}
