// Validates a storyboard BEFORE recording (no browser needed): unknown actions or fields, missing
// required fields, captions too long for the band, rushed clicks/drags, zooms never undone,
// files that do not exist. Exits 1 when there are errors (warnings alone exit 0).
//
// usage: node lint.mjs <storyboard.json> [--tools <dir>] [--strict]
//   --strict  treat warnings as errors
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';

// action -> { req: required fields, opt: optional fields }
export const SCHEMA = {
  title: { req: ['title'], opt: ['subtitle', 'say'] },
  goto: { req: [], opt: ['url', 'file', 'waitMs'], oneOf: ['url', 'file'] },
  caption: { req: ['text'], opt: ['label', 'say', 'shot', 'extraMs'] },
  uncaption: { req: [], opt: [] },
  click: { req: ['selector'], opt: ['focus'] },
  spotlight: { req: ['selector'], opt: ['padding', 'radius', 'ms'] },
  unspotlight: { req: [], opt: [] },
  hover: { req: ['selector'], opt: ['ms'] },
  type: { req: ['selector', 'text'], opt: ['delayMs', 'clear'] },
  select: { req: ['selector', 'value'], opt: [] },
  scroll: { req: ['to'], opt: ['offset', 'keepCaption', 'ms'] },
  zoom: { req: [], opt: ['selector', 'scale'] },
  unzoom: { req: [], opt: [] },
  drag: { req: ['selector'], opt: ['dx', 'dy', 'grip', 'steps', 'ms'] },
  hscroll: { req: ['container', 'toSelector'], opt: ['offset', 'ms'] },
  wait: { req: ['ms'], opt: [] },
  shot: { req: ['name'], opt: [] },
  evaluate: { req: ['js'], opt: ['ms'] },
};
// Fields every step may carry. Keys starting with "_" are comments and always allowed.
export const COMMON = ['action', 'expect', 'holdMs', 'note'];
export const EXPECT_KEYS = ['visible', 'hidden', 'text', 'url', 'timeoutMs'];
const HOLDS = new Set(['caption', 'wait', 'shot']);

export function lint(story, { storyDir = '.', toolsDir } = {}) {
  const out = [];
  const add = (level, where, msg) => out.push({ level, where, msg });
  const cfg = story.config ?? {};
  const W = cfg.viewport?.width ?? 1280;
  const capPx = cfg.style?.captionPx ?? Math.round(34 * W / 1440);
  const perLine = Math.floor((0.85 * W) / (capPx * 0.5)); // rough: average glyph ~0.5 em
  const baseDir = resolve(storyDir, cfg.baseDir ?? '.');
  const hold = cfg.holdAfterActionMs ?? 400;
  if (!Array.isArray(story.scenes) || !story.scenes.length) add('error', 'storyboard', '"scenes" must be a non-empty array');
  if (cfg.holdAfterActionMs !== undefined && !(cfg.holdAfterActionMs >= 0)) add('error', 'config', 'holdAfterActionMs must be a number >= 0');

  for (const [si, scene] of (story.scenes ?? []).entries()) {
    const steps = scene.steps ?? [];
    if (!Array.isArray(scene.steps)) add('error', `scene ${si + 1}`, '"steps" must be an array');
    let zoomed = null;
    steps.forEach((s, i) => {
      const where = `scene ${si + 1} "${scene.name ?? ''}", step ${i + 1} (${s.action})`;
      const def = SCHEMA[s.action];
      if (!def) { add('error', where, `unknown action "${s.action}". Known: ${Object.keys(SCHEMA).join(', ')}`); return; }
      for (const f of def.req) if (s[f] === undefined || s[f] === null) add('error', where, `missing required field "${f}"`);
      if (def.oneOf && !def.oneOf.some((f) => s[f])) add('error', where, `needs one of: ${def.oneOf.join(', ')}`);
      const allowed = new Set([...COMMON, ...def.req, ...def.opt]);
      for (const f of Object.keys(s)) if (!allowed.has(f) && !f.startsWith('_')) add('error', where, `unknown field "${f}" for action "${s.action}" (allowed: ${[...allowed].join(', ')})`);
      for (const f of ['ms', 'waitMs', 'extraMs', 'delayMs', 'holdMs', 'dx', 'dy', 'steps', 'offset', 'scale'])
        if (s[f] !== undefined && typeof s[f] !== 'number') add('error', where, `"${f}" must be a number`);

      if (s.action === 'caption' && typeof s.text === 'string') {
        const n = s.text.length;
        if (n > perLine * 2) add('error', where, `caption has ${n} chars, over 2 lines (~${perLine} per line at ${W}px): shorten it`);
        else if (n > perLine) add('warn', where, `caption has ${n} chars, wraps to 2 lines (~${perLine} per line at ${W}px)`);
        if (s.shot && !/^[\w.-]+$/.test(s.shot)) add('warn', where, `shot name "${s.shot}" has characters unsafe in file names`);
      }
      if (s.action === 'goto' && s.file) {
        const p = isAbsolute(s.file) ? s.file : join(baseDir, s.file);
        if (!existsSync(p)) add('error', where, `file not found: ${p}`);
      }
      if (s.action === 'zoom') {
        zoomed = i;
        if (s.scale && cfg.maxZoom !== undefined && s.scale > cfg.maxZoom) add('warn', where, `scale ${s.scale} is capped to maxZoom ${cfg.maxZoom}`);
        if (s.scale && cfg.maxZoom === undefined && s.scale > 1.1) add('warn', where, `scale ${s.scale} is capped to the default maxZoom 1.1 (set config.maxZoom)`);
      }
      // The camera also resets itself on scroll and navigation.
      if (['unzoom', 'goto', 'title', 'scroll'].includes(s.action)) zoomed = null;
      if (s.action === 'unzoom' && zoomed === null && !steps.slice(0, i).some((x) => x.action === 'zoom')) add('warn', where, 'unzoom without a previous zoom');

      if (s.expect !== undefined) {
        const list = Array.isArray(s.expect) ? s.expect : [s.expect];
        for (const e of list) {
          if (!e || typeof e !== 'object') { add('error', where, 'expect must be an object (or a list of objects)'); continue; }
          for (const k of Object.keys(e)) if (!EXPECT_KEYS.includes(k)) add('error', where, `unknown expect key "${k}" (known: ${EXPECT_KEYS.join(', ')})`);
          if (!Object.keys(e).some((k) => k !== 'timeoutMs')) add('error', where, 'empty expect');
          if (e.text !== undefined && !(Array.isArray(e.text) && e.text.length === 2 && e.text.every((x) => typeof x === 'string'))) add('error', where, 'expect.text must be [selector, substring]');
          if (e.url !== undefined && typeof e.url !== 'string') add('error', where, 'expect.url must be a string');
        }
      }
      if (s.action === 'click' || s.action === 'drag') {
        const next = steps[i + 1];
        const eff = s.holdMs ?? hold;
        const covered = next && HOLDS.has(next.action);
        if (!covered && eff < 600 && (!next || next.action === 'click' || next.action === 'drag'))
          add('warn', where, next ? `${s.action} is followed straight by another ${next.action}: add a wait/caption or holdMs >= 600` : `${s.action} ends the scene with no hold or caption after it`);
      }
    });
    if (zoomed !== null) add('error', `scene ${si + 1} "${scene.name ?? ''}"`, `zoom at step ${zoomed + 1} is never undone: add an unzoom before the scene ends`);
  }
  if (cfg.voice?.model) {
    const m = cfg.voice.model;
    const found = isAbsolute(m) ? existsSync(m) : [toolsDir && join(resolve(toolsDir), 'voices', m), join(baseDir, m)].some((p) => p && existsSync(p));
    if (!found) add(toolsDir || isAbsolute(m) ? 'error' : 'warn', 'config.voice', `voice model not found: ${m}${toolsDir ? '' : ' (pass --tools to check it)'}`);
  }
  return out;
}

export function report(issues) {
  for (const x of issues) console.log(`${x.level === 'error' ? 'ERROR' : 'warn '}  ${x.where}: ${x.msg}`);
  const e = issues.filter((x) => x.level === 'error').length, w = issues.length - e;
  console.log(`lint: ${e} error(s), ${w} warning(s)`);
  return e;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2);
  const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
  const toolsDir = flag('--tools');
  const strict = argv.includes('--strict');
  const [p] = argv.filter((a) => !a.startsWith('--'));
  if (!p) { console.error('usage: node lint.mjs <storyboard.json> [--tools dir] [--strict]'); process.exit(2); }
  let story;
  try { story = JSON.parse(readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch (e) { console.error(`ERROR  cannot read/parse ${p}: ${e.message}`); process.exit(1); }
  const issues = lint(story, { storyDir: dirname(resolve(p)), toolsDir });
  const errors = report(issues);
  process.exit(errors || (strict && issues.length) ? 1 : 0);
}
