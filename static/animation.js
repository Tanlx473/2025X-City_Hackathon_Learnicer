class AnimationEngine {
  constructor(canvas) {
    if (!canvas) {
      throw new Error('Canvas 元素不存在');
    }
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.isPlaying = false;
    this.requestId = null;
    this.time = 0;
    this.duration = 0;
    this.lastTimestamp = null;

    this.motionType = 'projectile';
    this.v0 = 0;
    this.angle = 0;
    this.g = 9.8;
    this.initialX = 0;
    this.initialY = 0;
    this.scale = 20;

    this.trajectoryPoints = [];
    this.pointsPath = [];
    this.pointDuration = 5;
  }

  static normalizePayload(raw) {
    if (!raw) return null;

    if (Array.isArray(raw)) {
      return {
        type: 'projectile',
        initial_speed: 16,
        angle: 50,
        gravity: 9.8,
        initial_x: 0,
        initial_y: 0,
        scale: 22,
        duration: 4,
      };
    }

    if (typeof raw === 'object') {
      if (raw.animation) return raw.animation;
      return raw;
    }

    return null;
  }

  loadInstructions(data) {
    const normalized = AnimationEngine.normalizePayload(data);
    if (!normalized) {
      throw new Error('动画指令为空或格式不支持');
    }

    this.motionType = normalized.type || 'projectile';
    this.v0 = normalized.initial_speed || normalized.v0 || 0;
    this.angle = ((normalized.angle ?? normalized.theta ?? 0) * Math.PI) / 180;
    this.g = normalized.gravity || 9.8;
    this.initialX = normalized.initial_x || normalized.x0 || 0;
    this.initialY = normalized.initial_y || normalized.y0 || 0;
    this.scale = normalized.scale || 20;
    this.duration = normalized.duration || 0;

    if (Array.isArray(normalized.points)) {
      this.pointsPath = normalized.points.map((p) => ({ x: p.x ?? p[0] ?? 0, y: p.y ?? p[1] ?? 0 }));
      if (!this.duration) this.duration = normalized.point_duration || this.pointDuration;
    } else {
      this.pointsPath = [];
    }

    if (!this.duration && this.motionType === 'projectile') {
      const vy0 = this.v0 * Math.sin(this.angle);
      this.duration = vy0 > 0 ? (2 * vy0) / this.g : 0;
    }

    this.reset();
    this.drawSceneInitial();
  }

  clearCanvas() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  drawGrid() {
    const spacing = 40;
    this.ctx.strokeStyle = '#e5e7eb';
    this.ctx.lineWidth = 1;
    for (let x = 0; x <= this.canvas.width; x += spacing) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.canvas.height);
      this.ctx.stroke();
    }
    for (let y = 0; y <= this.canvas.height; y += spacing) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.canvas.width, y);
      this.ctx.stroke();
    }
  }

  drawSceneInitial() {
    this.drawGrid();
    this.ctx.strokeStyle = '#d1d5db';
    this.ctx.lineWidth = 2;
    const groundY = this.toCanvasY(0);
    this.ctx.beginPath();
    this.ctx.moveTo(0, groundY);
    this.ctx.lineTo(this.canvas.width, groundY);
    this.ctx.stroke();

    this.ctx.fillStyle = '#9ca3af';
    this.ctx.font = '12px sans-serif';
    this.ctx.fillText('y = 0', 8, groundY - 6);
  }

  toCanvasX(x) {
    const offsetX = 50;
    return offsetX + x * this.scale;
  }

  toCanvasY(y) {
    const offsetY = 50;
    const groundY = this.canvas.height - offsetY;
    return groundY - y * this.scale;
  }

  drawObject(x, y) {
    const canvasX = this.toCanvasX(x);
    const canvasY = this.toCanvasY(y);
    const radius = 8;
    this.ctx.fillStyle = '#ef4444';
    this.ctx.beginPath();
    this.ctx.arc(canvasX, canvasY, radius, 0, 2 * Math.PI);
    this.ctx.fill();
  }

  drawVelocityVector(x, y, vx, vy) {
    const startX = this.toCanvasX(x);
    const startY = this.toCanvasY(y);
    const factor = 0.4;
    const endX = startX + vx * this.scale * factor;
    const endY = startY - vy * this.scale * factor;

    this.ctx.strokeStyle = '#2563eb';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.moveTo(startX, startY);
    this.ctx.lineTo(endX, endY);
    this.ctx.stroke();

    const angle = Math.atan2(startY - endY, endX - startX);
    const headlen = 10;
    this.ctx.beginPath();
    this.ctx.moveTo(endX, endY);
    this.ctx.lineTo(endX - headlen * Math.cos(angle - Math.PI / 6), endY + headlen * Math.sin(angle - Math.PI / 6));
    this.ctx.lineTo(endX - headlen * Math.cos(angle + Math.PI / 6), endY + headlen * Math.sin(angle + Math.PI / 6));
    this.ctx.lineTo(endX, endY);
    this.ctx.fillStyle = '#2563eb';
    this.ctx.fill();
  }

  drawTrajectory() {
    if (this.trajectoryPoints.length < 2) return;
    this.ctx.strokeStyle = '#f97316';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.trajectoryPoints.forEach((point, index) => {
      const x = this.toCanvasX(point[0]);
      const y = this.toCanvasY(point[1]);
      if (index === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });
    this.ctx.stroke();
  }

  computeProjectile(t) {
    const vx0 = this.v0 * Math.cos(this.angle);
    const vy0 = this.v0 * Math.sin(this.angle);
    const x = this.initialX + vx0 * t;
    const y = this.initialY + vy0 * t - 0.5 * this.g * t * t;
    const vx = vx0;
    const vy = vy0 - this.g * t;
    return { x, y, vx, vy };
  }

  computeUniform(t) {
    const x = this.initialX + this.v0 * t;
    const y = this.initialY;
    return { x, y, vx: this.v0, vy: 0 };
  }

  computePoints(t) {
    if (!this.pointsPath.length) return { x: this.initialX, y: this.initialY, vx: 0, vy: 0 };
    const clamped = Math.min(Math.max(t, 0), this.duration);
    const progress = this.duration ? clamped / this.duration : 0;
    const totalSegments = this.pointsPath.length - 1;
    const scaledIndex = progress * totalSegments;
    const idx = Math.floor(scaledIndex);
    const nextIdx = Math.min(idx + 1, this.pointsPath.length - 1);
    const localT = scaledIndex - idx;
    const start = this.pointsPath[idx];
    const end = this.pointsPath[nextIdx];
    const x = start.x + (end.x - start.x) * localT;
    const y = start.y + (end.y - start.y) * localT;
    const vx = (end.x - start.x) / (this.duration / totalSegments || 1);
    const vy = (end.y - start.y) / (this.duration / totalSegments || 1);
    return { x, y, vx, vy };
  }

  animate(timestamp) {
    if (!this.isPlaying) return;
    if (!this.lastTimestamp) this.lastTimestamp = timestamp;
    const delta = (timestamp - this.lastTimestamp) / 1000;
    this.lastTimestamp = timestamp;
    this.time += delta;

    this.clearCanvas();
    this.drawSceneInitial();

    let state = { x: this.initialX, y: this.initialY, vx: 0, vy: 0 };
    if (this.motionType === 'uniform') {
      state = this.computeUniform(this.time);
    } else if (this.motionType === 'points') {
      state = this.computePoints(this.time);
    } else {
      state = this.computeProjectile(this.time);
    }

    this.trajectoryPoints.push([state.x, state.y]);

    if (this.duration && this.time >= this.duration) {
      this.isPlaying = false;
    }

    this.drawTrajectory();
    this.drawObject(state.x, state.y);
    this.drawVelocityVector(state.x, state.y, state.vx, state.vy);

    if (this.isPlaying) {
      this.requestId = requestAnimationFrame(this.animate.bind(this));
    }
  }

  play() {
    if (this.isPlaying) return;
    this.isPlaying = true;
    this.lastTimestamp = null;
    this.requestId = requestAnimationFrame(this.animate.bind(this));
  }

  pause() {
    this.isPlaying = false;
    if (this.requestId) {
      cancelAnimationFrame(this.requestId);
      this.requestId = null;
    }
  }

  reset() {
    this.pause();
    this.time = 0;
    this.lastTimestamp = null;
    this.trajectoryPoints = [];
    this.clearCanvas();
    this.drawSceneInitial();
  }
}
