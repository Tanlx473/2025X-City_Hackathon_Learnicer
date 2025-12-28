class Uniform extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.vx = params.vx;      // x 方向速度
    this.vy = params.vy;      // y 方向速度
    this.x0 = params.x0;      // 初始 x
    this.y0 = params.y0;      // 初始 y
    this.mass = params.mass;  // 质量
    this.duration = params.duration;  // 总时长
    this.showVelocity = params.showVelocity || true;
    this.showAcceleration = params.showAcceleration || false;
    this.g = params.g || 0;  // 修改：添加 g=0 以兼容 gForce
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: this.x0, y: this.y0 },
      velocity: { x: this.vx, y: this.vy },
      acceleration: { x: 0, y: 0 },
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'green'
    }];
    
    this.trail = [];
    this.time = 0;
    this.isEnded = false;
  }
  
  update(dt) {
    if (this.isEnded) return;
    
    const obj = this.objects[0];
    
    // 匀速：位置 = 初位置 + v * t
    obj.position.x = this.x0 + this.vx * this.time;
    obj.position.y = this.y0 + this.vy * this.time;
    
    // 记录轨迹
    if (this.time % 0.1 < dt) {
      this.trail.push({ x: obj.position.x, y: obj.position.y });
    }
    
    // 如果有 duration，结束
    if (this.duration && this.time >= this.duration) {
      this.isEnded = true;
    }
  }
  
  draw() {
    super.draw();
    if (this.showAcceleration) {
      // 加速度为0，显示零向量或文字
      const obj = this.objects[0];
      const x = this.toCanvasX(obj.position.x);
      const y = this.toCanvasY(obj.position.y);
      
      this.ctx.fillStyle = 'green';
      this.ctx.font = '12px SimHei';
      this.ctx.fillText('a=0', x + 15, y - 15);
    }
  }
}