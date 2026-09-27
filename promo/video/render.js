// Renders film.html frame-by-frame (deterministic timeline) and pipes JPEG frames into ffmpeg.
// usage: node render.js <ffmpeg> <out.mp4> [audio.wav] | node render.js --stills t1,t2,... <outdir>
const { chromium } = require(process.env.PW || 'playwright');
const { spawn } = require('child_process');
const path = require('path');
const FPS = 30, DUR = 15;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'film.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);

  if (process.argv[2] === '--stills') {
    for (const t of process.argv[3].split(',').map(Number)) {
      await p.evaluate(t => render(t), t);
      await p.screenshot({ path: path.join(process.argv[4], `still-${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
    }
    return b.close();
  }

  const [ff, out, wav] = process.argv.slice(2);
  const args = ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-'];
  if (wav) args.push('-i', wav);
  args.push('-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
            '-movflags', '+faststart');
  if (wav) args.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push(out);
  const enc = spawn(ff, args, { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let f = 0; f < FPS * DUR; f++) {
    await p.evaluate(t => render(t), f / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!enc.stdin.write(buf)) await new Promise(r => enc.stdin.once('drain', r));
    if (f % 60 === 0) process.stderr.write(`frame ${f}/${FPS * DUR}\n`);
  }
  enc.stdin.end();
  await new Promise(r => enc.on('close', r));
  await b.close();
})();
