/* ============================================================
   竞拍之王 — 主游戏逻辑
   玩法：物品上架后买家自动出价，玩家在合适的价格落锤成交。
   卖太低 = 亏本；价格冲太高 = 无人接盘流拍。
   ============================================================ */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const money = (n) => '¥' + Math.round(n).toLocaleString('zh-CN');
  const SAVE_KEY = 'auction-king-save-v1';

  const G = {
    state: 'menu',        // menu | intro | bid | fall | hammer | result
    level: 0,
    gold: 0,
    stars: [0, 0, 0],
    unlocked: 1,
    queue: [],            // 本关物品下标
    idx: 0,               // 第几件
    item: null,
    bidders: [],
    price: 0,
    bids: 0,
    score: 0,             // 本关累计得分
    bidTimer: null,
    fallTimer: null,
    fallInterval: null,
  };

  /* ---------- 工具 ---------- */
  function pickWeighted(arr, weights) {
    let total = 0;
    for (const w of weights) total += w;
    let r = Math.random() * total;
    for (let i = 0; i < arr.length; i++) {
      r -= weights[i];
      if (r <= 0) return arr[i];
    }
    return arr[arr.length - 1];
  }

  /* ---------- 存档 ---------- */
  function loadSave() {
    try {
      const s = JSON.parse(localStorage.getItem(SAVE_KEY) || 'null');
      if (s) {
        G.gold = s.gold || 0;
        G.stars = s.stars || [0, 0, 0];
        G.unlocked = s.unlocked || 1;
      }
    } catch (e) { /* 忽略损坏存档 */ }
  }
  function saveSave() {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({
        gold: G.gold, stars: G.stars, unlocked: G.unlocked,
      }));
    } catch (e) { /* 忽略 */ }
  }

  /* ---------- HUD ---------- */
  function updateHUD() {
    $('hudGold').textContent = Math.round(G.gold).toLocaleString('zh-CN');
    $('hudLevelChip').textContent = '第 ' + (G.level + 1) + ' 关';
    $('hudProgress').textContent = '第 ' + (G.idx + 1) + ' / ' + G.queue.length + ' 件';
    $('hudScoreVal').textContent = G.score;
  }

  /* ---------- 观众席 ---------- */
  function buildBidderRow() {
    const row = $('bidderRow');
    row.innerHTML = '';
    for (let i = 0; i < 6; i++) {
      const d = document.createElement('div');
      d.className = 'bidder';
      d.id = 'bidder-' + i;
      d.innerHTML =
        '<div class="bubble"></div>' +
        '<div class="avatar">❓</div>' +
        '<div class="bname">…</div>' +
        '<div class="bstyle"></div>' +
        '<div class="bcount">出价 0 次</div>';
      row.appendChild(d);
    }
  }

  function renderBidders() {
    for (let i = 0; i < 6; i++) {
      const el = $('bidder-' + i);
      el.classList.remove('out', 'active-bid', 'empty');
      el.querySelector('.bubble').classList.remove('show');
      if (i < G.bidders.length) {
        const b = G.bidders[i];
        el.querySelector('.avatar').textContent = b.emoji;
        el.querySelector('.bname').textContent = b.name;
        el.querySelector('.bstyle').textContent = b.style;
        el.querySelector('.bcount').textContent = '出价 0 次';
        el.title = b.style + '买家 · “' + b.quote + '”';
      } else {
        el.classList.add('empty');
      }
    }
  }

  function animateBid(b, step) {
    const el = $('bidder-' + b.index);
    el.classList.remove('active-bid');
    void el.offsetWidth;
    el.classList.add('active-bid');
    const bubble = el.querySelector('.bubble');
    bubble.textContent = '+' + step;
    bubble.classList.remove('show');
    void bubble.offsetWidth;
    bubble.classList.add('show');
    el.querySelector('.bcount').textContent = '出价 ' + b.bids + ' 次';
  }

  function markOut(b) {
    if (!b.active) return;
    b.active = false;
    const el = $('bidder-' + b.index);
    el.classList.add('out');
    el.querySelector('.bstyle').textContent = '弃拍';
    const bubble = el.querySelector('.bubble');
    bubble.textContent = '🙅 弃拍';
    bubble.classList.remove('show');
    void bubble.offsetWidth;
    bubble.classList.add('show');
  }

  /* ---------- 物品 / 价格 UI ---------- */
  function renderItem() {
    const it = G.item;
    const emojiEl = $('itemEmoji');
    if (it.image) {
      emojiEl.innerHTML = '<img src="' + it.image + '" alt="' + it.name + '">';
    } else {
      emojiEl.textContent = it.emoji;
    }
    $('itemName').textContent = it.name;
    $('itemDesc').textContent = it.desc;
    $('itemBase').textContent = '起拍价 ' + money(it.base);
    $('sweetHint').textContent = '期望成交 ' + money(it.sweetLo) + ' – ' + money(it.sweetHi);
    $('fallText').textContent = '';
    updatePriceUI();
    const card = $('itemCard');
    card.classList.remove('show');
    void card.offsetWidth;
    card.classList.add('show');
  }

  function updatePriceUI() {
    const v = $('priceValue');
    v.textContent = money(G.price);
    v.classList.remove('sweet', 'warn', 'pop');
    void v.offsetWidth;
    v.classList.add('pop');
    if (G.price >= G.item.sweetLo && G.price <= G.item.sweetHi) v.classList.add('sweet');
    else if (G.price > G.item.sweetHi) v.classList.add('warn');
  }

  /* ---------- 流程 ---------- */
  function startItem() {
    clearTimers();
    G.item = ITEMS[G.queue[G.idx]];
    G.bidders = makeBidders(LEVELS[G.level].crowd, G.item);
    G.price = G.item.base;
    G.bids = 0;
    renderBidders();
    renderItem();
    $('stage').classList.remove('shake');
    setHammerMode('intro');
    updateHUD();
    G.state = 'intro';
    toast('物品上架！点击「开始竞拍」');
  }

  function beginBidding() {
    G.state = 'bid';
    setHammerMode('bid');
    scheduleNextBid();
    toast('竞拍开始！');
  }

  function scheduleNextBid() {
    clearTimeout(G.bidTimer);
    const it = G.item;
    const minStep = Math.max(10, Math.round(it.base * 0.04));
    const elig = G.bidders.filter(b => b.active && b.psych >= G.price + minStep);
    if (!elig.length) { startFall(); return; }

    /* 价格越低节奏越快；越过期望区间后买家开始犹豫 */
    let delay;
    if (G.price < it.sweetLo) delay = 650 + Math.random() * 850;
    else if (G.price <= it.sweetHi) delay = 950 + Math.random() * 1050;
    else delay = 1400 + Math.random() * 1300;
    G.bidTimer = setTimeout(() => doBid(elig), delay);
  }

  function doBid(elig) {
    const it = G.item;
    /* 冲动/土豪/神秘型买家更容易抢着出价 */
    const weights = elig.map(b =>
      (b.style === '保守' || b.style === '理性' || b.style === '识货') ? 1 : 1.7
    );
    const b = pickWeighted(elig, weights);
    const step = Math.max(10,
      Math.round(it.base * 0.045 * b.stepMult * (0.7 + Math.random() * 0.9) / 10) * 10);
    G.price += step;
    G.bids++;
    b.bids++;
    AudioFX.bid();
    animateBid(b, step);
    updatePriceUI();

    /* 超过心理价的买家弃拍 */
    const minStep = Math.max(10, Math.round(it.base * 0.04));
    G.bidders.forEach(x => {
      if (x.active && x.psych < G.price + minStep) markOut(x);
    });
    scheduleNextBid();
  }

  /* 流拍倒计时：再无人出价则流拍（玩家仍可抢在倒计时内落锤） */
  function startFall() {
    if (G.state === 'fall') return;
    G.state = 'fall';
    $('fallWrap').classList.add('on');
    const bar = $('fallBar');
    bar.style.transition = 'none';
    bar.style.width = '100%';
    requestAnimationFrame(() => requestAnimationFrame(() => {
      bar.style.transition = 'width 2.6s linear';
      bar.style.width = '0%';
    }));
    $('fallText').textContent = '⚠ 再没人出价就要流拍了！';
    G.fallInterval = setInterval(() => AudioFX.tick(), 600);
    G.fallTimer = setTimeout(endFall, 2600);
  }

  function endFall() {
    if (G.state !== 'fall') return;   /* 已被玩家落锤抢先 */
    settle('fall');
  }

  /* 玩家落锤 */
  function hammer() {
    if (G.state !== 'bid' && G.state !== 'fall') return;
    clearTimers();
    G.state = 'hammer';
    setHammerMode('idle');
    $('hammerBtn').classList.add('hit');
    $('stage').classList.add('shake');
    AudioFX.hammer();
    setTimeout(() => {
      $('hammerBtn').classList.remove('hit');
      $('stage').classList.remove('shake');
      settle('normal');
    }, 430);
  }

  /* ---------- 结算 ---------- */
  function settle(outcome) {
    if (G.state === 'result') return;
    clearTimers();
    const it = G.item, p = G.price;
    let grade, score, gain, title, msg;

    if (outcome === 'fall') {
      grade = 'fall'; score = 0; gain = -100;
      title = '流拍'; msg = '无人继续出价，物品遗憾流拍';
    } else if (p >= it.sweetLo && p <= it.sweetHi) {
      grade = 'perfect'; score = 100; gain = 200 + Math.round(p * 0.2);
      title = '完美成交！'; msg = '正中买家心理价位，全场掌声雷动';
    } else if (p < it.sweetLo) {
      if (p >= it.sweetLo * 0.85) {
        grade = 'good'; score = 65; gain = Math.round(p * 0.15);
        title = '成交略亏'; msg = '价格稍低，买家捡了个便宜';
      } else {
        grade = 'poor'; score = 30; gain = Math.round(p * 0.1);
        title = '卖亏了'; msg = '这也太便宜了，亏大发了';
      }
    } else {
      grade = 'over'; score = 50; gain = Math.round(p * 0.12);
      title = '溢价成交'; msg = '买家有点上头，小心他们事后反悔';
    }

    G.score += score;
    G.gold += gain;
    G.state = 'result';
    updateHUD();

    if (outcome === 'fall') AudioFX.fail();
    else { AudioFX.sold(); if (gain > 0) setTimeout(() => AudioFX.coin(), 350); }

    if (G.idx >= G.queue.length - 1) showLevelEnd(grade, score, gain, title, msg, p);
    else showResult(grade, score, gain, title, msg, p);
  }

  const GRADE_META = {
    perfect: { label: '完美成交', icon: '🌟', cls: 'perfect' },
    good:    { label: '略亏',     icon: '👍', cls: 'good' },
    poor:    { label: '卖亏了',   icon: '😅', cls: 'poor' },
    over:    { label: '溢价成交', icon: '😬', cls: 'over' },
    fall:    { label: '流拍',     icon: '💨', cls: 'fall' },
  };

  function showResult(grade, score, gain, title, msg, price) {
    const m = GRADE_META[grade];
    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">${G.item.emoji}</div>
        <h2>${title}</h2>
        <div class="grade-badge ${m.cls}">${m.icon} ${m.label}</div>
      </div>
      <div class="panel-rows">
        <div class="row"><span>成交价</span><b>${money(price)}</b></div>
        <div class="row"><span>本件得分</span><b class="score">+${score}</b></div>
        <div class="row"><span>佣金</span><b class="${gain >= 0 ? 'gain' : 'loss'}">${gain >= 0 ? '+' : ''}${money(gain)}</b></div>
      </div>
      <div class="panel-msg">${msg}</div>
      <button class="btn primary" id="btnNext">下一件 ▶</button>
    `;
    showOverlay();
    $('btnNext').onclick = () => { hideOverlay(); G.idx++; startItem(); };
  }

  function showLevelEnd(grade, score, gain, title, msg, price) {
    const lv = LEVELS[G.level];
    const total = G.score;
    let stars = 0;
    if (total >= 450) stars = 3;
    else if (total >= 320) stars = 2;
    else if (total >= 200) stars = 1;
    const pass = stars >= 1;

    if (stars > G.stars[G.level]) G.stars[G.level] = stars;
    if (pass && G.level + 1 > G.unlocked && G.level < LEVELS.length - 1) G.unlocked = G.level + 2;
    saveSave();

    const starHTML = '⭐'.repeat(stars) + '☆'.repeat(3 - stars);
    const isLast = G.level === LEVELS.length - 1;
    const nextBtnHTML = pass
      ? (isLast
          ? '<button class="btn primary" id="btnNext">🏆 全部通关！从头再玩</button>'
          : '<button class="btn primary" id="btnNext">下一关：' + LEVELS[G.level + 1].name + ' ▶</button>')
      : '<button class="btn primary" id="btnNext">🔁 重试本关</button>';

    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">${pass ? '🎉' : '😵'}</div>
        <h2>${pass ? '本关结算' : '业绩不达标'}</h2>
        <div class="grade-badge stars">${starHTML}</div>
      </div>
      <div class="panel-rows">
        <div class="row"><span>${lv.name}</span><b>${G.idx + 1} / ${G.queue.length} 件</b></div>
        <div class="row"><span>本关总得分</span><b class="score">${total} / 500</b></div>
        <div class="row"><span>累计金币</span><b class="gain">${money(G.gold)}</b></div>
      </div>
      <div class="panel-msg">${pass
        ? (stars >= 3 ? '金牌拍卖师的实力！' : stars === 2 ? '相当不错的表现！' : '勉强过关，继续加油！')
        : '得分太低，老板很不满意。再练练吧。'}</div>
      ${nextBtnHTML}
      <button class="btn ghost" id="btnMenu">回到主菜单</button>
    `;
    showOverlay();
    $('btnNext').onclick = () => {
      hideOverlay();
      if (pass && !isLast) G.level++;
      startLevel(isLast && pass ? 0 : G.level);
    };
    $('btnMenu').onclick = () => { hideOverlay(); showMainMenu(); };
  }

  /* ---------- 关卡 / 菜单 ---------- */
  function startLevel(lv) {
    hideOverlay();
    G.level = lv;
    G.queue = LEVELS[lv].items.slice();
    G.idx = 0;
    G.score = 0;
    startItem();
  }

  function showMainMenu() {
    clearTimers();
    G.state = 'menu';
    const lvCards = LEVELS.map((lv, i) => {
      const locked = i + 1 > G.unlocked;
      const stars = '⭐'.repeat(G.stars[i]) + '☆'.repeat(3 - G.stars[i]);
      return `
        <div class="level-card ${locked ? 'locked' : ''}" data-lv="${i}">
          <div class="lv-num">第 ${i + 1} 关</div>
          <div class="lv-name">${lv.name}</div>
          <div class="lv-desc">${lv.desc}</div>
          <div class="lv-stars">${locked ? '🔒' : stars}</div>
        </div>`;
    }).join('');
    $('panel').innerHTML = `
      <div class="logo">🔨</div>
      <h1>竞拍之王</h1>
      <div class="sub">Auction King · 拍卖师模拟器</div>
      <div class="howto">
        <div>1️⃣ 物品上架，买家们会轮流举手出价</div>
        <div>2️⃣ 每件物品都有<b>期望成交区间</b>（价格牌下方有提示）</div>
        <div>3️⃣ 在合适的时机<b>果断落锤</b>（点按钮或按空格）</div>
        <div>4️⃣ 卖太低亏本，等太久<b>流拍</b></div>
      </div>
      <div class="level-list">${lvCards}</div>
      <div class="hud-gold-line">🪙 金币 <b>${money(G.gold)}</b>　·　按 M 开关音效</div>
      <button class="btn primary" id="btnStart">▶ 开始第 ${G.unlocked} 关</button>
    `;
    showOverlay();
    $('btnStart').onclick = () => startLevel(G.unlocked - 1);
    document.querySelectorAll('.level-card').forEach(card => {
      card.onclick = () => {
        const lv = +card.dataset.lv;
        if (lv + 1 > G.unlocked) { toast('先通关前面的关卡吧'); return; }
        startLevel(lv);
      };
    });
  }

  /* ---------- 锤子按钮 ---------- */
  function setHammerMode(mode) {
    const btn = $('hammerBtn');
    const icon = $('hammerIcon');
    const label = $('hammerLabel');
    if (mode === 'intro') {
      btn.disabled = false;
      icon.textContent = '🎬';
      label.textContent = '开始竞拍';
    } else if (mode === 'bid') {
      btn.disabled = false;
      icon.textContent = '🔨';
      label.textContent = '落锤';
    } else {
      btn.disabled = true;
      icon.textContent = '🔨';
      label.textContent = '…';
    }
  }

  /* ---------- 杂项 ---------- */
  function clearTimers() {
    clearTimeout(G.bidTimer);
    clearTimeout(G.fallTimer);
    clearInterval(G.fallInterval);
    G.bidTimer = G.fallTimer = G.fallInterval = null;
    $('fallWrap').classList.remove('on');
    $('fallText').textContent = '';
  }

  function showOverlay() { $('overlay').classList.remove('hidden'); }
  function hideOverlay() { $('overlay').classList.add('hidden'); }

  let toastTimer = null;
  function toast(msg) {
    const t = $('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
  }

  function bindEvents() {
    $('hammerBtn').onclick = () => {
      AudioFX.ensure();
      if (G.state === 'intro') beginBidding();
      else if (G.state === 'bid' || G.state === 'fall') hammer();
    };
    $('btnMute').onclick = () => {
      AudioFX.ensure();
      AudioFX.muted = !AudioFX.muted;
      $('btnMute').textContent = AudioFX.muted ? '🔇' : '🔊';
    };
    document.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        AudioFX.ensure();
        if (G.state === 'intro') beginBidding();
        else if (G.state === 'bid' || G.state === 'fall') hammer();
        else if (G.state === 'result') {
          const b = $('btnNext');
          if (b) b.click();
        }
      } else if (e.code === 'KeyM') {
        $('btnMute').click();
      }
    });
    /* 首次交互时初始化音频上下文 */
    document.addEventListener('pointerdown', () => AudioFX.ensure(), { once: true });
  }

  /* ---------- 启动 ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    loadSave();
    buildBidderRow();
    bindEvents();
    updateHUD();
    showMainMenu();
  });
})();
