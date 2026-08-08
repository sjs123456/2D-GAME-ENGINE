/* 从候选清单下载物品图片到 img/（CC 授权图源，本地离线可用） */
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const list = JSON.parse(fs.readFileSync(path.join(__dirname, 'candidates.json'), 'utf8'));

function get(url, depth) {
  return new Promise((res) => {
    const mod = url.startsWith('https') ? https : http;
    const req = mod.get(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36' },
      timeout: 20000,
    }, (r) => {
      if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location && depth > 0) {
        r.resume();
        const loc = new URL(r.headers.location, url).href;
        return get(loc, depth - 1).then(res);
      }
      const chunks = [];
      r.on('data', c => chunks.push(c));
      r.on('end', () => res({ status: r.statusCode, buf: Buffer.concat(chunks), headers: r.headers }));
    });
    req.on('error', e => res({ status: 0, err: e.code || e.message }));
    req.on('timeout', () => { req.destroy(); res({ status: 0, err: 'timeout' }); });
  });
}

(async () => {
  const manifest = [];
  const failures = [];
  for (const [slug, meta] of Object.entries(list)) {
    try {
      const r = await get(meta.url, 3);
      if (r.status === 200 && r.buf && r.buf.length > 3000 && r.buf.length < 4 * 1024 * 1024) {
        const ct = (r.headers['content-type'] || '').toLowerCase();
        if (ct.includes('image') || /\.(jpe?g|png|webp)$/i.test(meta.url)) {
          fs.writeFileSync(path.join(__dirname, slug + '.jpg'), r.buf);
          manifest.push({ slug, name: meta.name, sizeKB: Math.round(r.buf.length / 1024), source: meta.url });
          console.log(`✅ ${slug.padEnd(9)} ${meta.name}  ${(r.buf.length / 1024).toFixed(0)}KB`);
          continue;
        }
      }
      failures.push(slug + ' (status ' + r.status + ' ' + (r.err || '') + ')');
    } catch (e) {
      failures.push(slug + ' (' + e.message + ')');
    }
  }
  fs.writeFileSync(path.join(__dirname, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log(`\n成功 ${manifest.length}/${Object.keys(list).length}`);
  if (failures.length) console.log('失败:', failures.join(' | '));
})();
