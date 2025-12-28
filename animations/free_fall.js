class FreeFall extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    // 兼容性：支持 height 或 h0
    this.h0 = params.height !== undefined ? params.height : (params.h0 !== undefined ? params.h0 : 10);
    this.g = params.g !== undefined ? params.g : 9.8;        // 重力加速度（默认值）
    this.mass = params.mass !== undefined ? params.mass : 1;  // 质量（默认值）
    this.bounce = params.bounce || false;  // 是否反弹
    this.bounceLoss = params.bounceLoss || 0.8;  // 能量损失系数
    this.showVelocity = params.showVelocity || true;
    this.showAcceleration = params.showAcceleration || false;
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: 5, y: this.h0 },  // x位置调整为5，避免靠边
      velocity: { x: 0, y: 0 },
      acceleration: { x: 0, y: -this.g },
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'red'
    }];
    
    this.trail = [];
    this.time = 0;
    this.isEnded = false;
  }
  
  update(dt) {
    if (this.isEnded) return;
    
    const obj = this.objects[0];
    
    // 更新速度
    obj.velocity.y += obj.acceleration.y * dt;
    
    // 更新位置
    obj.position.y += obj.velocity.y * dt;
    
    // 记录轨迹
    if (this.time % 0.1 < dt) {
      this.trail.push({ x: obj.position.x, y: obj.position.y });
    }
    
    // 落地检测
    if (obj.position.y <= 0) {
      obj.position.y = 0;
      if (this.bounce && Math.abs(obj.velocity.y) > 0.5) {
        obj.velocity.y = -obj.velocity.y * this.bounceLoss;
      } else {
        obj.velocity.y = 0;
        this.isEnded = true;  // 停止运动
      }
    }
  }
  
  draw() {
    super.draw();
    // 修改：移除旧的 showAcceleration 绘制，由 super 处理
  }
}