// Lays the voice-over lines on the recorded video at the times record.mjs logged, optionally adds a
// background music bed ducked under the voice, keeps the peak under -1 dBFS, and writes a WebM
// (VP8 + Opus) and an MP4 (H.264 + AAC, for PowerPoint/Teams).
// Needs a FULL ffmpeg (npm ffmpeg-static/ffprobe-static): Playwright's bundled one only encodes VP8.
//
// usage: node mix.mjs <outDir> [--ffmpeg <path>] [--ffprobe <path>] [--tools <dir>] [--music <file>]
//
// Music: `config.music` in the storyboard (copied into vo.json by record.mjs), or --music <file>:
//   { file, volume = 0.25, duckTo = 0.08, fadeIn = 1.5, fadeOut = 2.5 }
// The bed is first loudnormed to -16 LUFS (the voice level), so volume and duckTo are linear gains relative to the voice:
// 0.25 is about 12 dB under it. The ducking is a volume envelope built from
// the voice timeline (exact and repeatable, unlike a sidechain compressor whose depth depends on the
// voice level): the music glides down 0.25 s before each line and back up 0.6 s after it ends.
// Ideas from borjaperfra/launch-video-kit (loudnorm -16 LUFS / TP -1.5, measured ducking).
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve, isAbsolute } from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
let ffmpeg = flag('--ffmpeg'), ffprobe = flag('--ffprobe');
const tools = flag('--tools');
const musicFlag = flag('--music');
const [outArg] = argv;
if (!outArg) { console.error('usage: node mix.mjs <outDir> [--ffmpeg p] [--ffprobe p] [--tools dir] [--music file]'); process.exit(2); }
const outDir = resolve(outArg);

// Default: ffmpeg-static / ffprobe-static from <tools>/node_modules or cwd, else the PATH.
const fromNpm = (pkg, pick) => {
  for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return pick(createRequire(from)(pkg)); } catch { /* next */ }
  }
};
ffmpeg ??= fromNpm('ffmpeg-static', (m) => m) ?? 'ffmpeg';
ffprobe ??= fromNpm('ffprobe-static', (m) => m.path) ?? 'ffprobe';

const vo = JSON.parse(readFileSync(join(outDir, 'vo.json'), 'utf8'));
const { name, video: videoName, tEnd, lines } = vo;
const video = join(outDir, videoName);
const dur = Number(spawnSync(ffprobe, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], { encoding: 'utf8' }).stdout);
if (!(dur > 0)) throw new Error('could not read the video duration; check --ffprobe');
// Align the script clock with the video. record.mjs shows a magenta sync mark at the start and at the
// end and logs when each one ended (syncAt, syncEndAt, script clock). Here we find, in the video, the
// frame where each magenta run ends. The video is trimmed at the first mark and retimed by
// k = (video span between marks) / (script span between marks), because the recording does not run at
// exactly wall-clock speed: a fixed offset left the voice seconds early by the end of a 3-minute demo.
// After that, video time = script time - syncAt. Old recordings without marks fall back to an estimate.
const FPS = 50, SIDE = 4, FRAME = SIDE * SIDE * 3;
function magentaRuns(from, len) { // [end time of each magenta run] inside [from, from + len]
  const r = spawnSync(ffmpeg, ['-v', 'error', '-ss', String(Math.max(0, from)), '-t', String(len), '-i', video, '-vf', `fps=${FPS},scale=${SIDE}:${SIDE}`, '-pix_fmt', 'rgb24', '-f', 'rawvideo', 'pipe:1'], { maxBuffer: 1 << 27 });
  const buf = r.stdout ?? Buffer.alloc(0), ends = [];
  let prev = false;
  for (let i = 0; (i + 1) * FRAME <= buf.length; i++) {
    let R = 0, G = 0, B = 0;
    for (let p = 0; p < SIDE * SIDE; p++) { R += buf[i * FRAME + p * 3]; G += buf[i * FRAME + p * 3 + 1]; B += buf[i * FRAME + p * 3 + 2]; }
    const n = SIDE * SIDE, m = R / n > 180 && B / n > 180 && G / n < 90;
    if (prev && !m) ends.push(Math.max(0, from) + i / FPS);
    prev = m;
  }
  if (prev) ends.push(Math.max(0, from) + buf.length / FRAME / FPS);
  return ends;
}
const markA = vo.syncAt != null ? magentaRuns(0, 20)[0] ?? null : null;
const markB = markA != null && vo.syncEndAt != null ? magentaRuns(dur - 25, 25).at(-1) ?? null : null;
const trim = markA ?? 0;
const k = markB != null ? (markB - markA) / (vo.syncEndAt - vo.syncAt) : 1; // video seconds per script second
const lead = markA != null ? -vo.syncAt : Math.max(0, dur - tEnd - 0.3);
// With both marks, the output ends just before the end mark (it shows for 0.8 s before syncEndAt).
const vdur = markB != null ? vo.syncEndAt - 0.85 - vo.syncAt : (dur - trim) / k;
console.log(markA == null
  ? `video ${dur.toFixed(1)} s, logged ${tEnd.toFixed(1)} s, NO sync mark: estimated head start ${lead.toFixed(2)} s (may drift), ${lines.length} voice lines`
  : `video ${dur.toFixed(1)} s, sync marks at ${markA.toFixed(2)} s and ${markB?.toFixed(2) ?? '?'} s, speed ${k.toFixed(4)} (retimed), offset ${lead.toFixed(2)} s, ${lines.length} voice lines`);
if (Math.abs(k - 1) > 0.08) console.log(`warning: speed correction ${k.toFixed(3)} is large; check the sync marks in the raw video`);
const vin = trim > 0 ? ['-ss', trim.toFixed(3), '-i', video] : ['-i', video];
const vfilter = `setpts=(PTS-STARTPTS)/${k.toFixed(6)},trim=duration=${vdur.toFixed(3)}`;
const webmVideo = (trim > 0 || k !== 1) ? ['-c:v', 'libvpx', '-crf', '8', '-b:v', '6M', '-deadline', 'good', '-cpu-used', '4'] : ['-c:v', 'copy'];

const music = (musicFlag || vo.music) && {
  volume: 0.25, duckTo: 0.08, fadeIn: 1.5, fadeOut: 2.5, ...(vo.music ?? {}), ...(musicFlag ? { file: resolve(musicFlag) } : {}),
};
if (music && !(music.file && existsSync(music.file))) throw new Error(`music file not found: ${music?.file}`);
const n3 = (x) => Number(x).toFixed(3);

// Gain envelope for the music: `volume`, dipping to `duckTo` while a voice line plays.
// Per line: a trapezoid built from clip() ramps; max() over the lines; then volume - (volume - duckTo) * duck.
function duckExpr({ volume, duckTo }) {
  const ATTACK = 0.25, RELEASE = 0.6;
  const traps = lines.map((l) => {
    const s = l.at + lead, e = s + l.dur;
    return `min(clip((t-${n3(s - ATTACK)})/${ATTACK},0,1),clip((${n3(e + RELEASE)}-t)/${RELEASE},0,1))`;
  });
  if (!traps.length) return String(volume);
  const duck = traps.reduce((a, b) => `max(${a},${b})`);
  return `${n3(volume)}-${n3(volume - duckTo)}*${duck}`;
}

const outWebm = join(outDir, `${name}-voice.webm`), outMp4 = join(outDir, `${name}-voice.mp4`);
const run = (args, out) => {
  const r = spawnSync(ffmpeg, ['-y', '-v', 'error', ...args, out], { encoding: 'utf8' });
  if (r.status) throw new Error(r.stderr || String(r.error));
  console.log(out);
};
if (lines.length || music) {
  const inputs = [...vin];
  lines.forEach((l) => inputs.push('-i', l.file));
  const parts = [];
  if (lines.length) {
    lines.forEach((l, i) => { const ms = Math.max(0, Math.round((l.at + lead) * 1000)); parts.push(`[${i + 1}:a]adelay=${ms}|${ms}[a${i}]`); });
    parts.push(`${lines.map((_, i) => `[a${i}]`).join('')}amix=inputs=${lines.length}:normalize=0,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,pan=stereo|c0=0.707*c0|c1=0.707*c0[voice]`);
  }
  if (music) {
    const mi = lines.length + 1;
    inputs.push('-stream_loop', '-1', '-i', music.file); // looped, then trimmed to the video length below
    const fo = Math.min(music.fadeOut, vdur / 2), fi = Math.min(music.fadeIn, vdur / 2);
    parts.push(`[${mi}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:${n3(vdur)},asetpts=PTS-STARTPTS,highpass=f=100,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,` +
      `volume='${duckExpr(music)}':eval=frame,afade=t=in:d=${fi},afade=t=out:st=${n3(vdur - fo)}:d=${fo}[bed]`);
    parts.push(lines.length ? '[voice][bed]amix=inputs=2:normalize=0[mix]' : '[bed]anull[mix]');
  } else parts.push('[voice]anull[mix]');
  // The voice (mono) is loudnormed, then panned to stereo at -3 dB per channel (equal power, so the stereo programme still reads -16 LUFS), BEFORE the music joins, so the music never changes the voice level. The limiter
  // sits at -1.5 dBFS: lossy codecs overshoot the sample peak by ~0.3 dB, so the decoded peak stays under -1 dBFS.
  parts.push(`[mix]aresample=48000,alimiter=limit=0.84:attack=3:release=50:level=disabled,apad,atrim=0:${n3(vdur)}[aout]`);
  parts.push(`[0:v]${vfilter}[vout]`);
  const common = [...inputs, '-filter_complex', parts.join(';'), '-map', '[vout]', '-map', '[aout]'];
  run([...common, ...webmVideo, '-c:a', 'libopus', '-b:a', '128k'], outWebm);
  run([...common, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '25', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart'], outMp4);
} else { // captions only: no audio track
  console.log('no voice lines: writing captions-only video');
  run([...vin, '-vf', vfilter, ...webmVideo], outWebm);
  run([...vin, '-vf', vfilter, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '25', '-movflags', '+faststart'], outMp4);
}
// Overlaps would mean a line started before the previous one ended.
lines.forEach((l, i) => { if (i && l.at < lines[i - 1].at + lines[i - 1].dur) console.log(`overlap: "${lines[i - 1].text}" / "${l.text}"`); });
writeFileSync(join(outDir, 'mix.json'), JSON.stringify({ lead, trim, speed: k, marks: [markA, markB], duration: vdur, ffmpeg, ffprobe, webm: outWebm, mp4: outMp4, hasVoice: lines.length > 0, music: music ?? null }, null, 1));
