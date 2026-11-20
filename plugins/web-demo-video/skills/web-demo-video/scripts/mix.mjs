// Lays the voice-over lines on the recorded video at the times record.mjs logged, normalises the mix
// to -16 LUFS and writes a WebM (VP8 + Opus) and an MP4 (H.264 + AAC, for PowerPoint/Teams).
// Needs a FULL ffmpeg (npm ffmpeg-static/ffprobe-static): Playwright's bundled one only encodes VP8.
//
// usage: node mix.mjs <outDir> [--ffmpeg <path>] [--ffprobe <path>] [--tools <dir>]
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
let ffmpeg = flag('--ffmpeg'), ffprobe = flag('--ffprobe');
const tools = flag('--tools');
const [outArg] = argv;
if (!outArg) { console.error('usage: node mix.mjs <outDir> [--ffmpeg p] [--ffprobe p] [--tools dir]'); process.exit(2); }
const outDir = resolve(outArg);

// Default: ffmpeg-static / ffprobe-static from <tools>/node_modules or cwd, else the PATH.
const fromNpm = (pkg, pick) => {
  for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return pick(createRequire(from)(pkg)); } catch { /* next */ }
  }
};
ffmpeg ??= fromNpm('ffmpeg-static', (m) => m) ?? 'ffmpeg';
ffprobe ??= fromNpm('ffprobe-static', (m) => m.path) ?? 'ffprobe';

const { name, video: videoName, tEnd, lines } = JSON.parse(readFileSync(join(outDir, 'vo.json'), 'utf8'));
const video = join(outDir, videoName);
const dur = Number(spawnSync(ffprobe, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], { encoding: 'utf8' }).stdout);
if (!(dur > 0)) throw new Error('could not read the video duration; check --ffprobe');
// The video starts when the page is created, a moment before the script's clock: the difference
// between the video length and the logged end is that head start (0.3 s ~ time to close the context).
const lead = Math.max(0, dur - tEnd - 0.3);
console.log(`video ${dur.toFixed(1)} s, logged ${tEnd.toFixed(1)} s, head start ${lead.toFixed(2)} s, ${lines.length} voice lines`);

const outWebm = join(outDir, `${name}-voice.webm`), outMp4 = join(outDir, `${name}-voice.mp4`);
const run = (args, out) => {
  const r = spawnSync(ffmpeg, ['-y', '-v', 'error', ...args, out], { encoding: 'utf8' });
  if (r.status) throw new Error(r.stderr || String(r.error));
  console.log(out);
};
if (lines.length) {
  const inputs = ['-i', video];
  lines.forEach((l) => inputs.push('-i', l.file));
  const delays = lines.map((l, i) => { const ms = Math.round((l.at + lead) * 1000); return `[${i + 1}:a]adelay=${ms}|${ms}[a${i}]`; });
  const filter = `${delays.join(';')};${lines.map((_, i) => `[a${i}]`).join('')}amix=inputs=${lines.length}:normalize=0,` +
    'loudnorm=I=-16:TP=-1.5:LRA=11,apad[aout]';
  const common = [...inputs, '-filter_complex', filter, '-map', '0:v', '-map', '[aout]', '-shortest'];
  run([...common, '-c:v', 'copy', '-c:a', 'libopus', '-b:a', '128k'], outWebm);
  run([...common, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '25', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart'], outMp4);
} else { // captions only: no audio track
  console.log('no voice lines: writing captions-only video');
  run(['-i', video, '-c:v', 'copy'], outWebm);
  run(['-i', video, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '25', '-movflags', '+faststart'], outMp4);
}
// Overlaps would mean a line started before the previous one ended.
lines.forEach((l, i) => { if (i && l.at < lines[i - 1].at + lines[i - 1].dur) console.log(`overlap: "${lines[i - 1].text}" / "${l.text}"`); });
writeFileSync(join(outDir, 'mix.json'), JSON.stringify({ lead, duration: dur, ffmpeg, ffprobe, webm: outWebm, mp4: outMp4, hasVoice: lines.length > 0 }, null, 1));
