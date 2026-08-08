/* ============================================================
   竞拍之王 — 买家数据与心理价生成
   mult：心理价系数（相对期望区间上沿）
   stepMult：加价幅度系数
   ============================================================ */
const BIDDER_POOL = [
  { name: '王大爷',   emoji: '👴',  style: '保守', mult: 0.85, stepMult: 0.8, quote: '慢点慢点…' },
  { name: '李女士',   emoji: '💃',  style: '冲动', mult: 1.32, stepMult: 1.6, quote: '我要了！' },
  { name: '张老板',   emoji: '🤵',  style: '土豪', mult: 1.50, stepMult: 1.9, quote: '不差钱！' },
  { name: '小美',     emoji: '👩‍🦰', style: '理性', mult: 1.03, stepMult: 0.9, quote: '就值这个价' },
  { name: '神秘买家', emoji: '🕵️',  style: '神秘', mult: 1.18, stepMult: 1.3, quote: '电话委托，加' },
  { name: '陈教授',   emoji: '👓',  style: '识货', mult: 1.08, stepMult: 1.0, quote: '好东西！' },
  { name: '赵大婶',   emoji: '👵',  style: '跟风', mult: 0.92, stepMult: 0.7, quote: '我也凑个热闹' },
  { name: '外国友人', emoji: '🧔',  style: '豪爽', mult: 1.28, stepMult: 1.5, quote: 'Very good!' },
];

/* 为一件物品生成一批买家（每人一个心理价位，价格超过即弃拍） */
function makeBidders(crowdIdx, item) {
  return crowdIdx.map((pi, i) => {
    const tpl = BIDDER_POOL[pi];
    const psych = Math.max(
      Math.round(item.sweetLo * 0.82),
      Math.round(item.sweetHi * tpl.mult * (0.92 + Math.random() * 0.16))
    );
    return {
      index: i,
      name: tpl.name,
      emoji: tpl.emoji,
      style: tpl.style,
      quote: tpl.quote,
      mult: tpl.mult,
      stepMult: tpl.stepMult,
      psych: psych,
      bids: 0,
      active: true,
    };
  });
}
