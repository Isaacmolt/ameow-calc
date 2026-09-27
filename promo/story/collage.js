const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'collage.html'), { waitUntil: 'networkidle' });
  for (const id of ['a', 'b']) await p.locator('#' + id).screenshot({ path: path.join(__dirname, `collage-${id}.png`) });
  await b.close();
})();
