// Outputs from a recorded demo: subtitle files (SRT, VTT), an MP4 with scene chapters, an aspect preset
// (16:9, 1:1, 9:16), optional soft subtitles, and a small GIF. Run after record.mjs (and mix.mjs, if the video has voice).
//
// usage: node export.mjs <outDir> [--aspect 16:9|1:1|9:16] [--soft-subs] [--gif] [--gif-fps 8] [--gif-width 480] [--gif-from S] [--gif-seconds S]
//                        [--no-mp4] [--ffmpeg p] [--ffprobe p] [--tools dir]
//
// Writes to <outDir>/export/: <name>.srt, <name>.vtt, <name>-<aspect>.mp4 (chapters, optional mov_text track), <name>-<aspect>.gif
//
// Timing: a cue is shown from the caption's logged time to the time it faded, plus the same head start
// ("lead") that mix.mjs adds to voice lines. mix.mjs saves it in mix.json; without that file it is computed the same way.
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf(n); if (i < 0) return d; const [, v] = argv.splice(i, 2); return v; };
const bool = (n) => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
let ffmpeg = flag('--ffmpeg'), ffprobe = flag('--ffprobe');
const tools = flag('--tools');
const aspect = flag('--aspect', '16:9');
const gifFps = Number(flag('--gif-fps', 8)), gifWidth = Number(flag('--gif-width', 480));
const gifFrom = Number(flag('--gif-from', 0)), gifSecs = Number(flag('--gif-seconds', 0)); // 0 = to the end
const softSubs = bool('--soft-subs'), wantGif = bool('--gif'), noMp4 = bool('--no-mp4');
const [outArg] = argv;
if (!outArg || !['16:9', '1:1', '9:16'].includes(aspect)) {
  console.error('usage: node export.mjs <outDir> [--aspect 16:9|1:1|9:16] [--soft-subs] [--gif] [--gif-fps 8] [--gif-width 480] [--gif-from S] [--gif-seconds S] [--no-mp4] [--ffmpeg p] [--ffprobe p] [--tools dir]');
  process.exit(2);
}
const outDir = resolve(outArg);
const fromNpm = (pkg, pick) => {
  for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return pick(createRequire(from)(pkg)); } catch { /* next */ }
  }
};
ffmpeg ??= fromNpm('ffmpeg-static', (m) => m) ?? 'ffmpeg';
ffprobe ??= fromNpm('ffprobe-static', (m) => m.path) ?? 'ffprobe';
const sh = (bin, args) => { const r = spawnSync(bin, args, { encoding: 'utf8', maxBuffer: 1 << 26 }); if (r.status) throw new Error(r.stderr || String(r.error)); return r.stdout.trim(); };
const ff = (args) => sh(ffmpeg, ['-y', '-v', 'error', ...args]);
const probe = (file, what, key = 'format') => Number(sh(ffprobe, ['-v', 'error', '-show_entries', `${key}=${what}`, '-of', 'csv=p=0', file]));

const vo = JSON.parse(readFileSync(join(outDir, 'vo.json'), 'utf8'));
const timeline = JSON.parse(readFileSync(join(outDir, 'timeline.json'), 'utf8'));
const { name, tEnd, lines = [], scenes = [] } = vo;
// Source: the mixed MP4 (has the voice) if mix.mjs ran, else the raw WebM.
const mixed = join(outDir, `${name}-voice.mp4`);
const src = existsSync(mixed) ? mixed : join(outDir, vo.video);
const dur = probe(src, 'duration');
let lead;
if (existsSync(join(outDir, 'mix.json'))) lead = JSON.parse(readFileSync(join(outDir, 'mix.json'), 'utf8')).lead;
lead ??= Math.max(0, probe(join(outDir, vo.video), 'duration') - tEnd - 0.3); // same formula as mix.mjs
console.log(`source ${src}\n${dur.toFixed(1)} s, head start ${lead.toFixed(2)} s`);

const exp = join(outDir, 'export');
mkdirSync(exp, { recursive: true });

// ── Cues: every caption, plus voice lines that no caption covers (title cards) ───────────────
const cues = timeline.map((c) => ({ start: c.at + lead, end: (c.end ?? c.at + 3) + lead, text: c.text }));
for (const l of lines) {
  const s = l.at + lead;
  if (!cues.some((c) => s < c.end && s + l.dur > c.start)) cues.push({ start: s, end: s + l.dur + 0.3, text: l.text });
}
cues.sort((a, b) => a.start - b.start);
cues.forEach((c, i) => { // never overlap the next cue, never run past the video
  if (cues[i + 1]) c.end = Math.min(c.end, cues[i + 1].start - 0.04);
  c.end = Math.min(c.end, dur);
});
const ts = (t, sep) => {
  const ms = Math.round(Math.max(0, t) * 1000);
  const p = (n, w = 2) => String(n).padStart(w, '0');
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)}${sep}${p(ms % 1000, 3)}`;
};
// Long captions wrap in two balanced lines so players do not stretch them across the frame.
const wrap = (t) => {
  if (t.length <= 42) return t;
  const words = t.split(' '); let best = t, gap = Infinity, a = '';
  words.forEach((w, i) => { a += (i ? ' ' : '') + w; const b = words.slice(i + 1).join(' '); if (b && Math.abs(a.length - b.length) < gap) { gap = Math.abs(a.length - b.length); best = `${a}\n${b}`; } });
  return best;
};
const srt = cues.map((c, i) => `${i + 1}\n${ts(c.start, ',')} --> ${ts(c.end, ',')}\n${wrap(c.text)}\n`).join('\n');
const vtt = 'WEBVTT\n\n' + cues.map((c) => `${ts(c.start, '.')} --> ${ts(c.end, '.')}\n${wrap(c.text)}\n`).join('\n');
const srtPath = join(exp, `${name}.srt`), vttPath = join(exp, `${name}.vtt`);
writeFileSync(srtPath, srt); writeFileSync(vttPath, vtt);
console.log(`${srtPath}\n${vttPath}\n${cues.length} cues`);

// ── Chapters (FFMETADATA1): one per scene; the first starts at 0 so the intro is covered ───────
const chapters = scenes.map((s, i) => ({
  title: s.name,
  start: i === 0 ? 0 : s.at + lead,
  end: i + 1 < scenes.length ? scenes[i + 1].at + lead : dur,
}));
const meta = ';FFMETADATA1\n' + chapters.map((c) =>
  `[CHAPTER]\nTIMEBASE=1/1000\nSTART=${Math.round(c.start * 1000)}\nEND=${Math.round(c.end * 1000)}\ntitle=${c.title.replace(/[=;#\\\n]/g, (m) => '\\' + m)}\n`).join('');
const metaPath = join(exp, 'chapters.ffmetadata');
writeFileSync(metaPath, meta);

// ── Aspect presets ───────────────────────────────────────────────────────────────────────────
// 16:9 is untouched. 1:1 and 9:16 keep the WHOLE page: it is scaled to the output width and centred over a
// blurred, darkened copy of itself. A centred crop would cut 56% (1:1) or 68% (9:16) of a desktop page, so
// clicks, cursor and caption band would fall outside. The blurred pad loses nothing and looks intentional.
const outSize = { '16:9': null, '1:1': [1080, 1080], '9:16': [1080, 1920] }[aspect];
const aspectGraph = (inp = '[0:v]', outW = outSize?.[0]) => { // outW: GIFs build the pad at their own width, much cheaper
  if (!outSize) return outW ? `${inp}scale=${outW}:-2:flags=lanczos[v]` : `${inp}null[v]`;
  const w = outW & ~1, h = Math.round(outW * outSize[1] / outSize[0]) & ~1;
  return `${inp}split[bg][fg];[bg]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},boxblur=28:4,eq=brightness=-0.12[b];` +
    `[fg]scale=${w}:-2:flags=lanczos[f];[b][f]overlay=(W-w)/2:(H-h)/2[v]`;
};
const tag = aspect.replace(':', 'x');

if (!noMp4) {
  const out = join(exp, `${name}-${tag}.mp4`);
  const args = ['-i', src, '-i', metaPath];
  if (softSubs) args.push('-i', srtPath);
  args.push('-filter_complex', aspectGraph(), '-map', '[v]');
  if (sh(ffprobe, ['-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', src])) args.push('-map', '0:a', '-c:a', 'copy');
  if (softSubs) {
    const l3 = { es: 'spa', en: 'eng', fr: 'fra', de: 'deu', it: 'ita', pt: 'por' }[(vo.language || '').slice(0, 2)] ?? 'und';
    args.push('-map', '2:s', '-c:s', 'mov_text', '-metadata:s:s:0', `language=${l3}`, '-disposition:s:0', 'default');
  }
  args.push('-map_metadata', '1', '-map_chapters', '1', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '25', '-movflags', '+faststart');
  ff([...args, out]);
  console.log(`${out} ${(statSync(out).size / 1024).toFixed(0)} KB`);
}

// ── GIF: two passes. palettegen builds a 256-colour palette from the whole clip, paletteuse maps to it.
// A demo is mostly flat colour, so a global palette (stats_mode=diff favours the moving parts) and rectangle
// diffs keep the file small; bayer dithering compresses better than the default sierra.
if (wantGif) {
  const palette = join(exp, 'palette.png'), out = join(exp, `${name}-${tag}.gif`);
  const pre = `[0:v]fps=${gifFps}[x];${aspectGraph('[x]', gifWidth).replace('[v]', '[s]')}`;
  const clip = ['-ss', String(gifFrom), ...(gifSecs ? ['-t', String(gifSecs)] : [])];
  ff([...clip, '-i', src, '-filter_complex', `${pre};[s]palettegen=stats_mode=diff[p]`, '-map', '[p]', palette]);
  ff([...clip, '-i', src, '-i', palette, '-filter_complex', `${pre};[s][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle[g]`, '-map', '[g]', '-loop', '0', out]);
  console.log(`${out} ${(statSync(out).size / 1024).toFixed(0)} KB (${gifFps} fps, ${gifWidth} px wide)`);
}
