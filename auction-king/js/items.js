/* ============================================================
   竞拍之王 — 物品与关卡数据
   物品字段：
     name    名称
     emoji   图标（也可用 image 字段放真实图片 URL/路径）
     base    起拍价
     sweetLo / sweetHi   期望成交区间（落锤在此区间内 = 完美）
     desc    简介
   ============================================================ */
const ITEMS = [
  { name: '青花缠枝瓷瓶', emoji: '🏺', base: 500,  sweetLo: 700,  sweetHi: 950,  desc: '明宣德官窑，釉色如天青' },
  { name: '印象派油画',   emoji: '🖼️', base: 800,  sweetLo: 1100, sweetHi: 1500, desc: '《塞纳河晨雾》，笔触灵动' },
  { name: '祖母绿钻戒',   emoji: '💍', base: 1200, sweetLo: 1600, sweetHi: 2100, desc: '5 克拉哥伦比亚祖母绿' },
  { name: '鎏金座钟',     emoji: '🕰️', base: 350,  sweetLo: 500,  sweetHi: 680,  desc: '18 世纪法国宫廷座钟' },
  { name: '老式留声机',   emoji: '📻', base: 200,  sweetLo: 300,  sweetHi: 420,  desc: '手工橡木箱体，音色浑厚' },
  { name: '青铜古剑',     emoji: '🗡️', base: 900,  sweetLo: 1300, sweetHi: 1800, desc: '战国错金剑，品相完好' },
  { name: '鎏金佛像',     emoji: '🗿', base: 1500, sweetLo: 2000, sweetHi: 2700, desc: '宝相庄严，慈眉善目' },
  { name: '翡翠手镯',     emoji: '🪷', base: 1000, sweetLo: 1400, sweetHi: 1900, desc: '满绿冰种，水头十足' },
  { name: '古董怀表',     emoji: '⌚', base: 300,  sweetLo: 450,  sweetHi: 620,  desc: '瑞士机芯，走时精准' },
  { name: '紫砂大师壶',   emoji: '🍵', base: 400,  sweetLo: 600,  sweetHi: 820,  desc: '名家手制，包浆温润' },
  { name: '陨石标本',     emoji: '☄️', base: 700,  sweetLo: 1000, sweetHi: 1400, desc: '火星陨石，重 2.3 公斤' },
  { name: '手工小提琴',   emoji: '🎻', base: 600,  sweetLo: 850,  sweetHi: 1150, desc: '克雷莫纳制琴，音色甜美' },
];

/* 关卡：items 为 ITEMS 下标；crowd 为 BIDDER_POOL 下标 */
const LEVELS = [
  { name: '初入拍场', desc: '节奏平缓，新手热身',     items: [4, 8, 3, 9, 11], crowd: [0, 3, 5, 6] },
  { name: '风起云涌', desc: '买家各怀心思，看准时机', items: [0, 10, 1, 7, 2], crowd: [0, 1, 3, 4, 5] },
  { name: '大师之夜', desc: '土豪出手阔绰，小心上头', items: [5, 6, 2, 7, 0], crowd: [0, 1, 2, 4, 7] },
];
