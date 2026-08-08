/* ============================================================
   竞拍之王 BidKing — 数据层（v3 仓储盲盒）
   格子总数 20~120 可见；物品占 1~16 格隐藏；陷阱/惊喜机制
   ============================================================ */

/* 格子颜色线索（可见，基于"表面品质"，与真实价值约 85% 匹配） */
const COLOR_DEFS = {
  white:  { label: '白', color: '#cfd6dd', avg: 60,    desc: '几乎肯定是垃圾' },
  green:  { label: '绿', color: '#7ed68a', avg: 425,   desc: '普通货色' },
  blue:   { label: '蓝', color: '#6db3ff', avg: 1650,  desc: '有点东西' },
  purple: { label: '紫', color: '#c77dff', avg: 6000,  desc: '值钱的货' },
  gold:   { label: '金', color: '#ffd54a', avg: 21000, desc: '金色传说' },
  red:    { label: '红', color: '#ff5f5f', avg: 60000, desc: '大红！！' },
};
const COLOR_ORDER = ['white', 'green', 'blue', 'purple', 'gold', 'red'];

/* 物品真实品质（决定价值与占格；占格隐藏，开仓才揭示） */
const CONTENT_DEFS = {
  junk:   { label: '垃圾', color: '#9aa0a8', value: [0, 120],      size: [1, 2],   desc: '仿品 / 废品' },
  common: { label: '普通', color: '#8fd6a0', value: [150, 700],    size: [2, 4],   desc: '寻常物件' },
  rare:   { label: '稀有', color: '#6db3ff', value: [800, 2500],   size: [4, 6],   desc: '不错的藏品' },
  epic:   { label: '极品', color: '#c77dff', value: [3000, 9000],  size: [6, 10],  desc: '值钱的宝贝！' },
  legend: { label: '传说', color: '#ffd54a', value: [12000, 30000], size: [10, 14], desc: '镇仓之宝！！' },
  red:    { label: '大红', color: '#ff5f5f', value: [35000, 90000], size: [12, 16], desc: '天哪！大红出货！！！' },
};

/* 表面品质 → 颜色 */
const COLOR_CONTENT = {
  white: 'junk', green: 'common', blue: 'rare', purple: 'epic', gold: 'legend', red: 'red',
};

/* 物品池（名字 + 本地图片；真实品质独立随机） */
const ITEMS_POOL = [
  { name: '神秘纸箱',   image: 'box'     }, { name: '旧玩具熊',   image: 'teddy'   },
  { name: '旧油画',     image: 'painting'}, { name: '老座钟',     image: 'clock'   },
  { name: '木质收音机', image: 'radio'   }, { name: '紫砂壶',     image: 'teapot'  },
  { name: '青铜剑',     image: 'sword'   }, { name: '旧小提琴',   image: 'violin'  },
  { name: '青花瓷瓶',   image: 'vase'    }, { name: '钻戒',       image: 'ring'    },
  { name: '古钱币',     image: 'coin'    }, { name: '佛珠',       image: 'beads'   },
  { name: '鎏金怀表',   image: 'pocket'  }, { name: '石雕头像',   image: 'bust'    },
  { name: '王冠',       image: 'crown'   }, { name: '祖母绿宝石', image: 'emerald' },
  { name: '纯金鹰像',   image: 'eagle'   }, { name: '鎏金奖杯',   image: 'trophy'  },
  { name: '夜明珠',     image: 'pearl'   }, { name: '金匣',       image: 'jbox'    },
  { name: '老式相机',   image: 'camera'  }, { name: '机械手表',   image: 'mwatch'  },
  { name: '茶壶',       image: 'cteapot' }, { name: '玉雕',       image: 'jade'    },
];

/* 场次（门票 / 格数范围 / 品质概率 / 大仓回合数） */
const SCENES = [
  { id: 'low',    name: '低场·旧仓库', icon: '🏚️', ticket: 100,  grid: [20, 50],  funds: 30000,
    prob: { junk: 0.46, common: 0.28, rare: 0.16, epic: 0.07, legend: 0.03, red: 0.00 }, desc: '出货率低，练手热身' },
  { id: 'villa',  name: '别墅场',     icon: '🏡', ticket: 500,  grid: [30, 80],  funds: 80000,
    prob: { junk: 0.36, common: 0.28, rare: 0.20, epic: 0.11, legend: 0.04, red: 0.01 }, desc: '中规中矩，看颜色算数' },
  { id: 'ship',   name: '船运场',     icon: '🚢', ticket: 2000, grid: [40, 100], funds: 200000,
    prob: { junk: 0.30, common: 0.26, rare: 0.22, epic: 0.14, legend: 0.06, red: 0.02 }, desc: '集装箱盲盒，心跳加速' },
  { id: 'secret', name: '隐秘场',     icon: '🏛️', ticket: 8000, grid: [50, 120], funds: 400000,
    prob: { junk: 0.24, common: 0.24, rare: 0.24, epic: 0.18, legend: 0.08, red: 0.03 }, desc: '大佬对决，大红天堂' },
];

/* 玩家可选角色（技能） */
const ROLES = [
  { id: 'scout', name: '检索眼·贝拉', emoji: '🔍', skillName: '检索',
    desc: '每局 2 次：直接揭示 2 件物品的真实内容', count: 2 },
  { id: 'count', name: '数量师·维克托', emoji: '📐', skillName: '数格',
    desc: '每局 2 次：显示本仓高价值格（金/红）数量', count: 2 },
  { id: 'scan',  name: '透视师·伊森', emoji: '🗺️', skillName: '透视',
    desc: '每局 1 次：标出全部格子的表面成色是否可疑', count: 1 },
  { id: 'snipe', name: '截胡王·拉文', emoji: '🎯', skillName: '梭哈',
    desc: '每局 1 次：本轮 AI 无上限且碾压线再降；被动碾压线 -10%', count: 1 },
];

/* AI 对手 */
const AI_DEFS = [
  { id: 'boss', name: '张老板', emoji: '🤵', err: 0.20, mult: 1.18, greedy: 0,    quote: '大仓我全要！' },
  { id: 'li',   name: '李女士', emoji: '💃', err: 0.25, mult: 1.02, greedy: 0.30, quote: '红格必是大红！' },
  { id: 'prof', name: '陈教授', emoji: '👓', err: 0.07, mult: 0.96, greedy: 0,    quote: '颜色骗不了我' },
];

/* 每轮碾压比例（最高 ≥ 第二高 × ratio 直接成交），逐轮递减 */
const RATIO_BY_ROUND = [1.35, 1.40, 1.10];

/* 玩家可选倍率（相对当前最高价） */
const RATIO_OPTIONS = [1.05, 1.1, 1.15, 1.2, 1.3, 1.5];

/* ---------- 仓生成 ---------- */
function randInt(a, b) { return a + Math.floor(Math.random() * (b - a + 1)); }

function rollQuality(scene) {
  /* 按场次概率选"表面品质"，返回对应颜色名（格子颜色 = 表面品质） */
  const p = scene.prob;
  const order = ['junk', 'common', 'rare', 'epic', 'legend', 'red'];
  const colorOf = { junk: 'white', common: 'green', rare: 'blue', epic: 'purple', legend: 'gold', red: 'red' };
  let r = Math.random(), acc = 0;
  for (const q of order) {
    acc += p[q];
    if (r < acc) return colorOf[q];
  }
  return 'white';
}

/* 表面品质（决定格子颜色）→ 真实品质（决定价值与占格）：
   93% 一致；7% 陷阱（降 1 档）；5% 惊喜（升 1 档） */
function rollRealQuality(surface) {
  const i = COLOR_ORDER.indexOf(surface);
  const r = Math.random();
  if (r < 0.07) return COLOR_CONTENT[COLOR_ORDER[Math.max(0, i - 1)]];
  if (r < 0.12 && i < COLOR_ORDER.length - 1) return COLOR_CONTENT[COLOR_ORDER[i + 1]];
  return COLOR_CONTENT[surface];
}

function rollValue(type) {
  const d = CONTENT_DEFS[type];
  return Math.round((d.value[0] + Math.random() * (d.value[1] - d.value[0])) / 10) * 10;
}
function rollSize(type, maxLeft) {
  const d = CONTENT_DEFS[type];
  return Math.min(randInt(d.size[0], d.size[1]), maxLeft);
}

/* 生成一个仓：total 格（20~120），物品逐件占格（1~16）直至占满 */
function makeLot(scene, roundIdx, totalRounds) {
  const isBig = roundIdx >= totalRounds - 2;
  let total = randInt(scene.grid[0], scene.grid[1]);
  if (isBig) total = Math.min(120, Math.round(total * 1.25));

  const items = [];
  let used = 0;
  while (used < total) {
    const surface = rollQuality(scene);          /* 表面品质 → 格子颜色 */
    const real = rollRealQuality(surface);       /* 真实品质 → 价值/占格 */
    const size = rollSize(real, total - used);
    if (size < 1) break;
    const pool = ITEMS_POOL[Math.floor(Math.random() * ITEMS_POOL.length)];
    items.push({
      name: pool.name, image: pool.image,
      surface: surface, type: real,
      value: rollValue(real), size: size,
    });
    used += size;
  }

  /* 格子数组：每格颜色 = 表面品质 */
  const cells = [];
  items.forEach((it, idx) => {
    for (let i = 0; i < it.size; i++) cells.push({ color: it.surface, item: idx });
  });

  /* 起拍价 = 表面期望 × 0.20~0.28（低价买入空间，玩家可据此估算） */
  const expect = cells.reduce((s, c) => s + COLOR_DEFS[c.color].avg, 0);
  const start = Math.max(50, Math.round(expect * (0.20 + Math.random() * 0.08) / 10) * 10);
  return { cells: cells, items: items, start: start, expect: expect, total: cells.length, isBig: isBig };
}
