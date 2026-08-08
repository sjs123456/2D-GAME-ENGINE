/* ============================================================
   竞拍之王 BidKing — 程序化音效（Web Audio，零外部素材）
   ============================================================ */
const AudioFX = {
  ctx: null,
  muted: false,

  ensure() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();
  },

  tone(freq, dur, type, vol, glide) {
    if (this.muted || !this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    osc.type = type || 'sine';
    osc.frequency.setValueAtTime(freq, t);
    if (glide) osc.frequency.exponentialRampToValueAtTime(glide, t + dur);
    g.gain.setValueAtTime(vol || 0.2, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(g);
    g.connect(this.ctx.destination);
    osc.start(t);
    osc.stop(t + dur + 0.05);
  },

  noise(dur, vol, freq) {
    if (this.muted || !this.ctx) return;
    const t = this.ctx.currentTime;
    const len = Math.max(1, Math.floor(this.ctx.sampleRate * dur));
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len);
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    const filt = this.ctx.createBiquadFilter();
    filt.type = 'lowpass';
    filt.frequency.value = freq || 1200;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(vol || 0.3, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(filt); filt.connect(g); g.connect(this.ctx.destination);
    src.start(t);
  },

  /* —— 游戏音效 —— */
  bid()    { this.tone(480, 0.09, 'square', 0.05, 720); },
  seal()   { this.tone(300, 0.12, 'triangle', 0.15, 420); },
  hammer() { this.noise(0.22, 0.5, 900); this.tone(120, 0.3, 'sine', 0.5, 55); },
  coin()   { this.tone(988, 0.09, 'triangle', 0.16, 1319); },
  fail()   { this.tone(320, 0.35, 'sawtooth', 0.12, 140); },
  tick()   { this.tone(1250, 0.05, 'square', 0.05); },
  big()    {
    this.tone(523, 0.12, 'triangle', 0.22);
    setTimeout(() => this.tone(659, 0.12, 'triangle', 0.22), 110);
    setTimeout(() => this.tone(784, 0.3, 'triangle', 0.25), 220);
  },
};
