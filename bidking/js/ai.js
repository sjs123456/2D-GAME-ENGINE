/* ============================================================
   竞拍之王 BidKing — AI 决策（纯逻辑，无 DOM，可独立测试）
   ctx = { round, maxBid, minRaise, ratio, cap }
   节奏：轮 1 试探性压价，轮 2/3 贴碾压线竞争
   估值打 9 折：老手知道有陷阱，买入偏保守
   ============================================================ */
const AI = {

  /* 按可见颜色线索估算仓的期望价值（表面期望 × 0.9 陷阱折扣） */
  estimate(lot, p) {
    let v = 0;
    for (const c of lot.cells) {
      let avg = COLOR_DEFS[c.color].avg;
      if (p.greedy && (c.color === 'gold' || c.color === 'red')) avg *= 1 + p.greedy;
      v += avg * (1 + p.err * (Math.random() * 2 - 1));
    }
    return Math.max(10, Math.round(v * 0.9 / 10) * 10);
  },

  /* 单轮出价：返回金额；0 = 本轮放弃（下轮可再入场，观战截胡） */
  bid(lot, p, ctx) {
    const est = this.estimate(lot, p);
    if (ctx.round === 1) {
      if (est < lot.start * 0.85) return 0;
      /* 轮 1 试探性出价（留出轮 2/3 的抬价空间） */
      let bid = est * p.mult * (0.45 + Math.random() * 0.3);
      return this.clamp(bid, lot.start, ctx.cap, p.cash);
    }
    const floor = ctx.maxBid + ctx.minRaise;
    if (est < ctx.maxBid * 0.96) {
      /* 明显不值：三成概率贴线搏一把碾压，否则放弃 */
      if (Math.random() < 0.3 && p.cash >= ctx.maxBid * ctx.ratio) {
        return this.clamp(ctx.maxBid * ctx.ratio * (1 + Math.random() * 0.04), floor, ctx.cap, p.cash);
      }
      return 0;
    }
    if (ctx.round === 3 && Math.random() < 0.08) return 0;
    let bid = est * p.mult * (0.7 + Math.random() * 0.3);
    /* 三成概率贴碾压线（略上浮避免平局），制造碾压或刺刀局 */
    if (Math.random() < 0.3) bid = Math.max(bid, ctx.maxBid * ctx.ratio * (1.0 + Math.random() * 0.05));
    return this.clamp(bid, floor, ctx.cap, p.cash);
  },

  clamp(bid, lo, hi, cash) {
    if (hi != null) bid = Math.min(bid, hi);
    bid = Math.min(bid, cash);
    if (bid < lo) return 0;
    bid = Math.floor(bid / 10) * 10;
    if (bid < lo) return 0;
    return bid;
  },
};
