/* ============================================================
   竞拍之王 BidKing — 主游戏逻辑（v3）
   20~120 格盲盒仓 / 物品占格隐藏 / 每轮真实提示
   碾压成交（倍率出价）/ 逐件揭示（品质 loading + 一键跳过）
   ============================================================ */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const money = (n) => '¥' + Math.round(n).toLocaleString('zh-CN');
  const SAVE_KEY = 'bidking-save-v3';
  const TOTAL_ROUNDS = 5;

  const S = {
    state: 'menu',
    sceneIdx: 0, scene: null,
    round: 0, lot: null,
    bidRound: 1, maxBid: 0, minRaise: 50, ratio: 1.4, cap: null,
    leader: null, lotWinner: null,
    players: [], me: null,
    skill: { type: 'scout', left: 0, snipeOn: false },
    usedHints: [],
    unboxIdx: 0, unboxSum: 0, unboxTimer: null, unboxSkipped: false,
    timers: [],
    save: { unlocked: 1, cleared: [false, false, false, false], collection: [] },
  };

  /* ---------- 工具 ---------- */
  function later(fn, ms) { const t = setTimeout(fn, ms); S.timers.push(t); return t; }
  function clearTimers() {
    S.timers.forEach(clearTimeout);
    S.timers = [];
    clearTimeout(S.unboxTimer);
    S.unboxTimer = null;
  }
  function loadSave() {
    try {
      const s = JSON.parse(localStorage.getItem(SAVE_KEY) || 'null');
      if (s) S.save = Object.assign(S.save, s);
    } catch (e) { /* 忽略 */ }
  }
  function saveSave() {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(S.save)); } catch (e) { /* 忽略 */ }
  }

  /* ---------- HUD ---------- */
  function updateHUD() {
    $('hudScene').textContent = S.scene ? S.scene.icon + ' ' + S.scene.name : '—';
    $('hudRound').textContent = S.scene ? '回合 ' + Math.min(S.round, TOTAL_ROUNDS) + '/' + TOTAL_ROUNDS : '—';
    $('hudTicket').textContent = S.scene ? money(S.scene.ticket) : '—';
    $('hudCash').textContent = money(S.me ? S.me.cash : 0);
    updateSkillBtn();
  }

  function updateSkillBtn() {
    const btn = $('btnSkill');
    const meta = { scout: '🔍 检索', count: '📐 数格', scan: '🗺️ 透视', snipe: '🎯 梭哈' };
    btn.textContent = meta[S.skill.type] + (S.skill.left > 0 ? ' ×' + S.skill.left : '');
    const usable = S.state === 'lot_intro' && S.skill.left > 0;
    btn.disabled = !usable;
  }

  /* ---------- 玩家席位 ---------- */
  function renderPlayers() {
    const row = $('playersRow');
    row.innerHTML = '';
    S.players.forEach((p, i) => {
      const el = document.createElement('div');
      el.className = 'player' + (p.isMe ? ' me' : '') + (p === S.leader ? ' leader' : '');
      el.innerHTML =
        '<div class="p-avatar">' + p.emoji + '</div>' +
        '<div class="p-name">' + p.name + (p.isMe ? '（你）' : '') + '</div>' +
        '<div class="p-cash">' + money(p.cash) + '</div>' +
        '<div class="p-status">' + (p.status || '') + '</div>';
      row.appendChild(el);
    });
  }

  /* ---------- 仓网格（彩色格子，总格数可见） ---------- */
  function renderGrid(scanFlags) {
    const grid = $('lotGrid');
    grid.innerHTML = '';
    const cols = Math.min(12, Math.max(8, Math.ceil(Math.sqrt(S.lot.total) * 1.1)));
    grid.style.gridTemplateColumns = 'repeat(' + cols + ', 1fr)';
    S.lot.cells.forEach((c, i) => {
      const el = document.createElement('div');
      el.className = 'cell';
      el.dataset.i = i;
      el.style.background = 'linear-gradient(160deg, ' + lighten(COLOR_DEFS[c.color].color) + ', ' + COLOR_DEFS[c.color].color + ')';
      if (scanFlags && scanFlags[i]) {
        el.classList.add('mark', scanFlags[i]);
      }
      el.innerHTML = '<span class="cell-q">?</span>';
      el.title = COLOR_DEFS[c.color].label + '格 · ' + COLOR_DEFS[c.color].desc;
      grid.appendChild(el);
    });
  }

  function lighten(hex) {
    const n = parseInt(hex.slice(1), 16);
    const r = Math.min(255, (n >> 16) + 70), g = Math.min(255, ((n >> 8) & 255) + 70), b = Math.min(255, (n & 255) + 70);
    return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
  }

  /* ---------- 提示系统（全部真实线索，多样化） ---------- */
  function surfaceRank(c) { return COLOR_ORDER.indexOf(c.surface); }
  function realRank(it) { return ['junk','common','rare','epic','legend','red'].indexOf(it.type); }

  function makeHint() {
    const lot = S.lot;
    const goldRed = lot.cells.filter(c => c.color === 'gold' || c.color === 'red').length;
    const traps = lot.items.filter(it => realRank(it) < surfaceRank(it) - 0).filter(it => realRank(it) <= 1 && surfaceRank(it) >= 3).length;
    const surprises = lot.items.filter(it => realRank(it) > surfaceRank(it)).length;
    const big = lot.items.filter(it => it.size >= 8).length;
    const smallMany = lot.items.filter(it => it.size <= 3).length >= lot.items.length * 0.7;
    const reds = lot.items.filter(it => it.type === 'red').length;
    const legends = lot.items.filter(it => it.type === 'legend').length;
    const itemCount = lot.items.length;
    const cheapStart = lot.start < lot.expect * 0.55;
    const sample = lot.items[Math.floor(Math.random() * lot.items.length)];

    const pool = [
      { t: goldRed > 0,  s: '有人瞥见一抹金色光泽，但很快被杂物盖住了（金/红格 ' + goldRed + ' 个）' },
      { t: goldRed === 0, s: '这仓看起来灰扑扑的，连个亮色都没有' },
      { t: traps > 0,    s: '封条有被动过的痕迹——怕是有' + traps + ' 件货不对劲（表面光鲜）' },
      { t: surprises > 0, s: '有几件包装格外朴素的货，反常地讲究（可能有惊喜）' },
      { t: big >= 2,     s: '搬运工说这仓死沉，至少 ' + big + ' 件大家伙' },
      { t: big === 0,    s: '都是轻飘飘的零碎小件，没一件大货' },
      { t: smallMany,    s: '箱子码得密密麻麻，全是小件，翻起来费劲' },
      { t: reds > 0,     s: '灯影下闪过一道红光——有 ' + reds + ' 件大红货！！' },
      { t: reds === 0 && legends > 0, s: '有人闻到一股包浆的旧木香，像是传说级的老物件' },
      { t: itemCount >= 15, s: '货单厚厚一叠，约 ' + itemCount + ' 件物品，杂得很' },
      { t: itemCount < 8, s: '货单很薄，就 ' + itemCount + ' 件，但件件看着压秤' },
      { t: cheapStart,   s: '卖家急着出手，起拍价压得明显低于行情' },
      { t: true,         s: '角落里好像露出了「' + sample.name + '」的一角' },
      { t: goldRed >= 4, s: '光是金红色的格子就有 ' + goldRed + ' 个，灯下晃眼' },
      { t: traps === 0 && goldRed > 0, s: '这仓的金红格成色都很正，没看出做手脚的痕迹' },
      { t: lot.total >= 90, s: '一百来格的巨仓，仓库门口堆得满满当当' },
      { t: lot.total <= 35, s: '小仓，一眼望到底，但小仓常出奇货' },
      { t: surprises === 0 && traps === 0, s: '表面成色和货单对得上，规规矩矩的一仓' },
    ];
    const avail = pool.filter(p => p.t && !S.usedHints.includes(p.s));
    const pick = avail[Math.floor(Math.random() * avail.length)] || pool[0];
    S.usedHints.push(pick.s);
    return pick.s;
  }

  function showHint() {
    const el = $('lotHint');
    el.textContent = '💬 ' + makeHint();
    el.style.animation = 'none';
    void el.offsetWidth;
    el.style.animation = '';
  }

  /* ---------- 流程：回合 ---------- */
  function startRound() {
    clearTimers();
    S.lot = makeLot(S.scene, S.round, TOTAL_ROUNDS);
    /* 起拍价保底：不超过全场最有钱者现金的一半（保证竞价有抬价空间） */
    const maxCash = Math.max(...S.players.map(p => p.cash));
    if (S.lot.start > maxCash * 0.35) S.lot.start = Math.max(50, Math.round(maxCash * 0.35 / 10) * 10);

    S.bidRound = 1;
    S.maxBid = S.lot.start;
    S.minRaise = Math.max(50, Math.round(S.lot.start * 0.05 / 10) * 10);
    S.leader = null;
    S.lotWinner = null;
    S.skill.snipeOn = false;
    S.usedHints = [];
    S.players.forEach(p => { p.status = ''; });

    $('lotTitle').textContent = (S.lot.isBig ? '🔥 大仓 · ' : '') + '第 ' + S.round + ' 回合 · 神秘仓库';
    $('lotInfo').textContent = '共 ' + S.lot.total + ' 格 · 约 ' + S.lot.items.length + ' 件物品 · 起拍价 ' + money(S.lot.start);
    $('lotHint').textContent = '';
    $('lotSkill').textContent = '';
    $('revealRow').innerHTML = '';
    renderGrid();
    renderPlayers();
    updateHUD();
    S.state = 'lot_intro';
    $('btnStart').classList.remove('hidden');
    $('sealedUI').classList.add('hidden');
    $('waitMsg').classList.add('hidden');
    toast('第 ' + S.round + ' 回合开拍！格数 ' + S.lot.total + '，看颜色猜货');
  }

  function beginBidding() {
    if (S.state !== 'lot_intro') return;
    AudioFX.ensure();
    startBidRound();
  }

  /* ---------- 竞价轮（倍率出价 + 碾压线） ---------- */
  function startBidRound() {
    S.state = 'bid_input';
    $('btnStart').classList.add('hidden');
    $('waitMsg').classList.add('hidden');

    /* 碾压比例：截胡王被动 -0.10 */
    S.ratio = Math.max(1.05, RATIO_BY_ROUND[S.bidRound - 1] - (S.skill.type === 'snipe' ? 0.10 : 0));
    /* 本轮 AI 出价上限：仅轮 1 温和起步（1.3×起拍）；轮 2/3 自由竞价（受估值约束，天然有分布差） */
    S.cap = S.skill.snipeOn ? null
      : (S.bidRound === 1 ? Math.floor(S.maxBid * 1.3 / 10) * 10 : null);

    $('bidRoundNo').textContent = S.bidRound;
    $('curMax').textContent = money(S.maxBid);
    $('ratioLine').textContent = '⚡ 碾压线 ×' + S.ratio.toFixed(2) +
      '：最高 ≥ 第二高 ×' + S.ratio.toFixed(2) + ' 直接成交' + (S.skill.snipeOn ? '（梭哈模式：本轮无上限）' : '');

    renderRatioBtns();
    $('sealedUI').classList.remove('hidden');
  }

  function renderRatioBtns() {
    const box = $('ratioBtns');
    box.innerHTML = '';
    RATIO_OPTIONS.forEach(r => {
      const amt = Math.floor(S.maxBid * r / 10) * 10;
      const btn = document.createElement('button');
      btn.className = 'ratio-btn' + (Math.abs(r - S.ratio) < 0.001 ? ' line' : '');
      btn.textContent = r.toFixed(2).replace(/0$/, '') + '× ' + money(amt);
      btn.disabled = amt > S.me.cash;
      btn.onclick = () => submitRatio(r);
      box.appendChild(btn);
    });
    $('bidHint').textContent = S.skill.snipeOn
      ? '梭哈模式：可出任意价（≤ 现金 ' + money(S.me.cash) + '）'
      : (S.cap != null ? 'AI 本轮上限 ' + money(S.cap) : 'AI 自由竞价') + ' · 你可以更高倍率梭哈截胡！';
  }

  function submitRatio(r) {
    if (S.state !== 'bid_input') return;
    const amt = Math.floor(S.maxBid * r / 10) * 10;
    if (amt > S.me.cash) { toast('现金不够！'); return; }
    S.me.bid = amt;
    S.me.status = '已出价 ' + money(amt);
    collectBids();
  }

  function passBid() {
    if (S.state !== 'bid_input') return;
    S.me.bid = 0;
    S.me.status = '本轮放弃';
    collectBids();
  }

  function collectBids() {
    AudioFX.seal();
    $('sealedUI').classList.add('hidden');
    $('waitMsg').classList.remove('hidden');
    S.state = 'bid_wait';
    const ais = S.players.filter(p => !p.isMe);
    ais.forEach((p, i) => {
      later(() => {
        p.bid = AI.bid(S.lot, p, {
          round: S.bidRound,
          maxBid: S.maxBid,
          minRaise: S.minRaise,
          ratio: S.ratio,
          cap: S.skill.snipeOn ? null : S.cap,
        });
        p.status = p.bid > 0 ? '已出价' : '本轮放弃';
        renderPlayers();
      }, 450 * (i + 1));
    });
    later(() => revealBids(), 450 * (ais.length + 1) + 400);
  }

  function revealBids() {
    if (S.state !== 'bid_wait') return;
    S.state = 'bid_reveal';
    $('waitMsg').classList.add('hidden');
    const row = $('revealRow');
    row.innerHTML = '';
    const list = S.players.slice().sort((a, b) => (b.bid || 0) - (a.bid || 0));
    list.forEach((p, i) => {
      const card = document.createElement('div');
      card.className = 'bidcard';
      card.innerHTML =
        '<div class="bc-avatar">' + p.emoji + '</div>' +
        '<div class="bc-name">' + p.name + '</div>' +
        '<div class="bc-amount">' + (p.bid > 0 ? money(p.bid) : '放弃') + '</div>';
      row.appendChild(card);
      later(() => { card.classList.add('flip'); if (p.bid > 0) AudioFX.tick(); }, 220 + i * 380);
    });

    later(() => {
      const top = list[0];
      const topAmt = top.bid || 0;
      const secondAmt = list[1] ? (list[1].bid || 0) : 0;
      /* 碾压判定：最高 ≥ 第二高 × ratio（无第二高视为碾压） */
      const crushed = topAmt > 0 && (secondAmt === 0 || topAmt >= secondAmt * S.ratio);

      if (topAmt > 0) {
        S.maxBid = topAmt;
        S.leader = top;
        top.status = '领先 👑';
        row.children[0].classList.add('winner');
        renderPlayers();
        AudioFX.bid();
      }

      if (crushed) {
        toast('💥 碾压成交！');
        later(() => {
          row.innerHTML = '';
          finalizeLot();
        }, 1200);
      } else if (S.bidRound >= 3) {
        later(() => {
          row.innerHTML = '';
          finalizeLot();
        }, 1500);
      } else {
        /* 未碾压 → 弹出一条真实提示，进入下一轮 */
        later(() => {
          row.innerHTML = '';
          showHint();
          S.bidRound++;
          startBidRound();
        }, 1600);
      }
    }, 220 + list.length * 380 + 500);
  }

  /* ---------- 成交 + 逐件揭示 ---------- */
  function finalizeLot() {
    if (!S.leader) { toast('💨 无人出价，本仓流拍'); later(nextRound, 1400); return; }
    S.lotWinner = S.leader;
    S.lotWinner.cash -= S.maxBid;
    S.lotWinner.items.push({ lot: S.lot, pay: S.maxBid });
    S.lotWinner.status = '拍得！';
    AudioFX.hammer();
    renderPlayers();
    startUnbox();
  }

  function startUnbox() {
    S.state = 'unbox';
    S.unboxIdx = -1;
    S.unboxSum = 0;
    S.unboxSkipped = false;
    const buyer = S.lotWinner, it = S.lot.items;
    $('lotTitle').textContent = buyer.emoji + ' ' + buyer.name + ' 以 ' + money(S.maxBid) + ' 拍得 · 开仓！';
    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">📦</div>
        <h2>开仓 · 藏品逐件揭示</h2>
        <div class="sub">${buyer.name}${buyer.isMe ? '（你）' : ''} · 支付 ${money(S.maxBid)}</div>
      </div>
      <div id="unboxHead">已揭示 <b id="ubCount">0</b>/<b id="ubTotal">${it.length}</b> 件 · 累计价值 <b id="ubSum">${money(0)}</b></div>
      <div id="ubCard" class="loading">
        <div class="ub-spinner"><div class="ring"></div><div>正在鉴定…</div></div>
      </div>
      <div id="ubProgressWrap"><div id="ubProgress"></div></div>
      <button class="btn ghost" id="btnSkipUnbox">⚡ 一键查看全部</button>
    `;
    showOverlay();
    $('btnSkipUnbox').onclick = () => skipUnbox();
    revealNextItem();
  }

  function revealNextItem() {
    const items = S.lot.items;
    S.unboxIdx++;
    if (S.unboxIdx >= items.length) { unboxDone(); return; }
    const it = items[S.unboxIdx];
    const card = $('ubCard');
    const cd = CONTENT_DEFS[it.type];

    /* 展示：先模糊加载（loading 时长 = 品质越高越久） */
    const loadingMs = { junk: 600, common: 1000, rare: 1600, epic: 2400, legend: 3600, red: 5200 }[it.type];
    card.className = 'loading';
    card.style.borderColor = '#d4af37';
    card.innerHTML =
      '<img class="ub-img" src="img/' + it.image + '.jpg" alt="">' +
      '<div class="ub-spinner"><div class="ring"></div><div>正在鉴定…</div></div>';

    S.unboxTimer = setTimeout(() => {
      /* 揭示 */
      card.className = 'revealed';
      card.style.borderColor = cd.color;
      card.innerHTML =
        '<img class="ub-img" src="img/' + it.image + '.jpg" alt="">' +
        '<div class="ub-meta">' +
        '  <div class="ub-name">' + it.name + '<span class="ub-size">占 ' + it.size + ' 格</span></div>' +
        '  <div class="ub-type" style="color:' + cd.color + '">' + cd.label + '</div>' +
        '  <div class="ub-val">' + money(it.value) + '</div>' +
        '</div>';
      S.unboxSum += it.value;
      $('ubCount').textContent = S.unboxIdx + 1;
      $('ubSum').textContent = money(S.unboxSum);
      $('ubProgress').style.width = ((S.unboxIdx + 1) / items.length * 100) + '%';
      if (it.type === 'red' || it.type === 'legend') AudioFX.big();
      else if (it.type === 'epic') AudioFX.coin();
      else AudioFX.tick();
      S.unboxTimer = setTimeout(revealNextItem, 900);
    }, loadingMs);
  }

  function skipUnbox() {
    if (S.unboxSkipped) return;
    S.unboxSkipped = true;
    clearTimeout(S.unboxTimer);
    const items = S.lot.items;
    S.unboxSum = items.reduce((s, it) => s + it.value, 0);
    $('unboxHead').innerHTML = '已揭示 <b>' + items.length + '</b>/<b>' + items.length + '</b> 件 · 累计价值 <b>' + money(S.unboxSum) + '</b>';
    $('ubProgress').style.width = '100%';
    $('ubCard').style.display = 'none';
    const gridHTML = items.map(it => {
      const cd = CONTENT_DEFS[it.type];
      return '<div class="ub-all-item" style="border-color:' + cd.color + '">' +
        '<img src="img/' + it.image + '.jpg" alt="">' +
        '<div class="ua-name">' + it.name + '<span class="ua-size">' + it.size + '格</span></div>' +
        '<div class="ua-val" style="color:' + cd.color + '">' + money(it.value) + '</div>' +
        '</div>';
    }).join('');
    const head = $('panel').querySelector('.panel-head');
    const skipBtn = $('btnSkipUnbox');
    skipBtn.outerHTML = '<div id="ubAll">' + gridHTML + '</div>';
    unboxDone(true);
  }

  function unboxDone(skipped) {
    if (!skipped && S.unboxIdx < S.lot.items.length) return;
    const total = S.unboxSum;
    const diff = total - S.maxBid;
    const isLast = S.round >= TOTAL_ROUNDS;
    const def = diff >= 0 ? 'gain' : 'loss';
    const btn = document.createElement('button');
    btn.className = 'btn primary';
    btn.id = 'btnNext3';
    btn.textContent = isLast ? '查看本局结算' : '下一回合 ▶';
    btn.onclick = () => {
      hideOverlay();
      if (isLast) gameEnd();
      else nextRound();
    };
    $('panel').appendChild(btn);
    const head = $('panel').querySelector('.panel-head .sub');
    if (head) head.textContent = '仓内总价值 ' + money(total) + ' · ' + (diff >= 0 ? '赚 ' : '亏 ') + money(Math.abs(diff)) + ' ' + (diff >= 0 ? '🎉' : '💸');
  }

  function nextRound() {
    S.round++;
    if (S.round > TOTAL_ROUNDS) gameEnd();
    else startRound();
  }

  /* ---------- 技能 ---------- */
  function useSkill() {
    if (S.state !== 'lot_intro' || S.skill.left <= 0) return;
    const t = S.skill.type;
    if (t === 'scout') {
      const idxs = [];
      while (idxs.length < 2 && idxs.length < S.lot.items.length) {
        const i = Math.floor(Math.random() * S.lot.items.length);
        if (!idxs.includes(i)) idxs.push(i);
      }
      S.skill.left--;
      const info = idxs.map(i => {
        const it = S.lot.items[i];
        return '「' + it.name + '」' + money(it.value);
      }).join('　');
      $('lotSkill').textContent = '🔍 检索结果：' + info;
      AudioFX.coin();
      toast('🔍 检索到 2 件物品！');
    } else if (t === 'count') {
      const n = S.lot.cells.filter(c => c.color === 'gold' || c.color === 'red').length;
      S.skill.left--;
      $('lotSkill').textContent = '📐 金/红格数量：' + n + ' / ' + S.lot.total;
      AudioFX.coin();
      toast('📐 数格完成');
    } else if (t === 'scan') {
      S.skill.left--;
      const flags = {};
      S.lot.items.forEach(it => {
        const rReal = realRank(it), rSurf = surfaceRank(it);
        if (rReal <= 1 && rSurf >= 3) it._trap = true;   /* 表面光鲜实为垃圾 */
        if (rReal > rSurf) it._good = true;
      });
      /* 格子标记：物品对应的格子全部标出 */
      let cellIdx = 0;
      S.lot.items.forEach(it => {
        for (let k = 0; k < it.size; k++) {
          if (it._trap) flags[cellIdx + k] = 'trap';
          else if (it._good) flags[cellIdx + k] = 'good';
        }
        cellIdx += it.size;
      });
      renderGrid(flags);
      $('lotSkill').textContent = '🗺️ 透视完成：🔴=可疑（表面光鲜）　🟢=暗藏惊喜';
      AudioFX.coin();
      toast('🗺️ 可疑格已标出');
    } else if (t === 'snipe') {
      S.skill.left--;
      S.skill.snipeOn = true;
      $('lotSkill').textContent = '🎯 梭哈模式已激活：本轮出价无上限，碾压线降低！';
      AudioFX.big();
      toast('🎯 梭哈！');
    }
    updateSkillBtn();
  }

  /* ---------- 局结算 ---------- */
  function gameEnd() {
    S.players.forEach(p => {
      p.total = p.cash + p.items.reduce((s, x) => s + x.lot.items.reduce((a, it) => a + it.value, 0), 0);
    });
    const rank = S.players.slice().sort((a, b) => b.total - a.total);
    const meRank = rank.findIndex(p => p.isMe) + 1;
    const win = meRank === 1;
    if (win) {
      S.save.cleared[S.sceneIdx] = true;
      if (S.save.unlocked <= S.sceneIdx) S.save.unlocked = S.sceneIdx + 2;
    }
    S.players.forEach(p => {
      if (p.isMe) p.items.forEach(x => x.lot.items.forEach(it => S.save.collection.push({
        name: it.name, image: it.image, type: it.type, value: it.value,
      })));
    });
    saveSave();

    const rankHTML = rank.map((p, i) => `
      <div class="rank-row ${i === 0 ? 'first' : ''} ${p.isMe ? 'me' : ''}">
        <span class="rk">#${i + 1}</span>
        <span class="rk-emoji">${p.emoji}</span>
        <span class="rk-name">${p.name}${p.isMe ? '（你）' : ''}</span>
        <span class="rk-total">${money(p.total)}</span>
      </div>`).join('');
    const myLots = S.players.filter(p => p.isMe)[0].items;
    const isLast = S.sceneIdx >= SCENES.length - 1;
    let nextBtn;
    if (win && !isLast) nextBtn = `<button class="btn primary" id="btnNext4">下一场：${SCENES[S.sceneIdx + 1].name} ▶</button>`;
    else if (win && isLast) nextBtn = `<button class="btn primary" id="btnNext4">👑 成为竞拍之王！</button>`;
    else nextBtn = `<button class="btn primary" id="btnNext4">🔁 重试本场（再交门票）</button>`;

    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">${win ? (isLast ? '👑' : '🎉') : '😵'}</div>
        <h2>${win ? '本局盈利！' : '没赚到钱…'}</h2>
        <div class="sub">${S.scene.icon} ${S.scene.name} · 门票 ${money(S.scene.ticket)} · 排名第 ${meRank}</div>
      </div>
      <div class="rank-list">${rankHTML}</div>
      <div class="panel-rows">
        <div class="row"><span>本局拍得仓数</span><b>${myLots.length} / ${TOTAL_ROUNDS}</b></div>
        <div class="row"><span>剩余现金</span><b>${money(S.me.cash)}</b></div>
      </div>
      ${nextBtn}
      <button class="btn ghost" id="btnMenu4">回到主菜单</button>
    `;
    showOverlay();
    $('btnNext4').onclick = () => {
      hideOverlay();
      if (win && !isLast) startScene(S.sceneIdx + 1);
      else if (win && isLast) showWinScreen();
      else startScene(S.sceneIdx);
    };
    $('btnMenu4').onclick = () => { hideOverlay(); showMenu(); };
  }

  function showWinScreen() {
    const coll = S.save.collection;
    const collHTML = coll.length
      ? coll.slice(-24).map(x =>
        '<div class="ub-all-item" style="border-color:' + CONTENT_DEFS[x.type].color + '">' +
        '<img src="img/' + x.image + '.jpg" alt="">' +
        '<div class="ua-name">' + x.name + '</div>' +
        '<div class="ua-val" style="color:' + CONTENT_DEFS[x.type].color + '">' + money(x.value) + '</div>' +
        '</div>').join('')
      : '<span class="dim">空</span>';
    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">👑</div>
        <h2>竞拍之王诞生！</h2>
        <div class="sub">四张场全部问鼎 · 仓储盲盒的神</div>
      </div>
      <div class="collection-box">
        <div class="cb-title">🏆 我的收藏柜（${coll.length} 件）</div>
        <div id="ubAll">${collHTML}</div>
      </div>
      <button class="btn primary" id="btnAgain2">🎮 再来一局</button>
      <button class="btn ghost" id="btnMenu5">回到主菜单</button>
    `;
    showOverlay();
    $('btnAgain2').onclick = () => { hideOverlay(); showRoleSelect(); };
    $('btnMenu5').onclick = () => { hideOverlay(); showMenu(); };
  }

  /* ---------- 菜单 / 角色 / 进场 ---------- */
  function showMenu() {
    clearTimers();
    S.state = 'menu';
    const cards = SCENES.map((s, i) => {
      const locked = i + 1 > S.save.unlocked;
      const star = S.save.cleared[i] ? '✅' : (locked ? '🔒' : '🔓');
      return `
        <div class="level-card ${locked ? 'locked' : ''}" data-si="${i}">
          <div class="lv-num">第 ${i + 1} 场</div>
          <div class="lv-icon">${s.icon}</div>
          <div class="lv-mid">
            <div class="lv-name">${s.name}</div>
            <div class="lv-desc">${s.desc} · 门票 ${money(s.ticket)} · ${s.grid[0]}~${s.grid[1]} 格</div>
          </div>
          <div class="lv-stars">${star}</div>
        </div>`;
    }).join('');
    const coll = S.save.collection;
    $('panel').innerHTML = `
      <div class="logo">📦</div>
      <h1>竞拍之王</h1>
      <div class="sub">BidKing · 仓储盲盒拍卖</div>
      <div class="howto">
        <div>1️⃣ 每回合一个盲盒仓：<b>格数可见</b>（20~120），物品占格隐藏</div>
        <div>2️⃣ <b>倍率出价</b>：选当前价的倍数；高出第二多一定比例 = <b>碾压成交</b></div>
        <div>3️⃣ 每轮出价后都会出现<b>真实提示</b>，仔细听</div>
        <div>4️⃣ 拍下后<b>逐件开箱</b>：品质越高鉴定越久，可一键跳过</div>
      </div>
      <div class="level-list">${cards}</div>
      <div class="collection-line">🏆 收藏柜（${coll.length}）：${coll.slice(-14).map(x => '🖼').join('') || '<span class="dim">空</span>'}</div>
      <button class="btn primary" id="btnPlay">🎮 选择角色 · 进场</button>
    `;
    showOverlay();
    $('btnPlay').onclick = () => showRoleSelect();
    document.querySelectorAll('.level-card').forEach(card => {
      card.onclick = () => {
        const i = +card.dataset.si;
        if (i + 1 > S.save.unlocked) { toast('先赢下前面的场次吧'); return; }
        showRoleSelect(i);
      };
    });
  }

  function showRoleSelect(sceneIdx) {
    S.state = 'menu';
    const startIdx = sceneIdx == null ? Math.min(S.save.unlocked - 1, SCENES.length - 1) : sceneIdx;
    const cards = ROLES.map(r => `
      <div class="role-card" data-role="${r.id}">
        <div class="rc-emoji">${r.emoji}</div>
        <div class="rc-mid">
          <div class="rc-name">${r.name}</div>
          <div class="rc-desc">${r.desc}</div>
        </div>
      </div>`).join('');
    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">🎭</div>
        <h2>选择你的身份</h2>
        <div class="sub">即将进场：${SCENES[startIdx].icon} ${SCENES[startIdx].name}（门票 ${money(SCENES[startIdx].ticket)}）</div>
      </div>
      <div class="role-list">${cards}</div>
      <button class="btn ghost" id="btnBack">← 返回</button>
    `;
    showOverlay();
    document.querySelectorAll('.role-card').forEach(card => {
      card.onclick = () => startScene(startIdx, card.dataset.role);
    });
    $('btnBack').onclick = () => showMenu();
  }

  function startScene(idx, roleId) {
    hideOverlay();
    S.sceneIdx = idx;
    S.scene = SCENES[idx];
    S.round = 1;
    const role = ROLES.find(r => r.id === roleId) || ROLES[0];
    S.players = [
      { id: 'me', name: role.name, emoji: role.emoji, isMe: true, cash: S.scene.funds, items: [], status: '', bid: 0 },
      ...AI_DEFS.map(d => ({
        id: d.id, name: d.name, emoji: d.emoji, isMe: false, cash: S.scene.funds, items: [], status: '', bid: 0,
        err: d.err, mult: d.mult, greedy: d.greedy,
      })),
    ];
    S.me = S.players[0];
    S.skill = { type: role.id, left: role.count, snipeOn: false };
    S.players.forEach(p => { p.cash -= S.scene.ticket; });
    renderPlayers();
    updateHUD();
    $('panel').innerHTML = `
      <div class="panel-head">
        <div class="big-emoji">${S.scene.icon}</div>
        <h2>${S.scene.name}</h2>
        <div class="sub">${S.scene.desc} · ${TOTAL_ROUNDS} 回合 · 门票 ${money(S.scene.ticket)} 已扣除</div>
      </div>
      <div class="howto">
        <div>对手：${S.players.filter(p => !p.isMe).map(p => p.emoji + ' ' + p.name).join('　')}</div>
        <div>目标：5 回合后总资产 <b>排名第一</b>，赚回门票钱</div>
      </div>
      <button class="btn primary" id="btnEnter">进入拍卖场</button>
    `;
    showOverlay();
    $('btnEnter').onclick = () => { hideOverlay(); startRound(); };
  }

  /* ---------- 杂项 ---------- */
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
    $('btnStart').onclick = () => beginBidding();
    $('btnBid').onclick = () => { const el = document.querySelector('.ratio-btn:not(:disabled)'); if (el) el.click(); };
    $('btnPass').onclick = () => passBid();
    $('btnSkill').onclick = () => { AudioFX.ensure(); useSkill(); };
    $('btnMute').onclick = () => {
      AudioFX.ensure();
      AudioFX.muted = !AudioFX.muted;
      $('btnMute').textContent = AudioFX.muted ? '🔇' : '🔊';
    };
    document.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        AudioFX.ensure();
        if (S.state === 'lot_intro') beginBidding();
      } else if (e.code === 'KeyM') {
        $('btnMute').click();
      }
    });
    document.addEventListener('pointerdown', () => AudioFX.ensure(), { once: true });
  }

  /* ---------- 启动 ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    loadSave();
    bindEvents();
    showMenu();
  });
})();
