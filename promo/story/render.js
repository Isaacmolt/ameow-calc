// Renders each .story section of stories.html to story-N.png (1080×1920).
const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'stories.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  for (const i of [1, 2, 3]) await p.locator('#s' + i).screenshot({ path: path.join(__dirname, `story-${i}.png`) });
  await b.close();
})();
