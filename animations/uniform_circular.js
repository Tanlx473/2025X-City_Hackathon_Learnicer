class UniformCircular extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.radius = params.radius;      // 半径 r
    this.omega = params.omega;        // 角速度 ω
    this.mass = params.mass;          // 质量 m
    this.mu = params.mu || 0.5;       // 摩擦系数 μ (假设提供向心力)
    this.g = params.g || 9.8;         // 重力加速度
    this.center = { x: params.centerX || canvas.width / (2 * this.config.scale), y: params.centerY || canvas.height / (2 * this.config.scale) }; // 圆心
    this.initialAngle = params.initialAngle || 0; // 初始角度
    this.duration = params.duration || 10; // 总时长
    this.v = this.radius * this.omega; // 线速度 v = r ω
    this.centripetal = this.mass * this.v**2 / this.radius; // 向心力 Fc = m v^2 / r
    this.Fn = this.mass * this.g; // 支撑力 Fn = mg (假设水平圆周)
    this.f_max = this.mu * this.Fn; // 最大静摩擦力 f_max = μ Fn (提供向心力)
    // 假设 f = Fc, 如果 f > f_max 则无法维持匀速圆周，但这里假设合适
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: this.center.x + this.radius * Math.cos(this.initialAngle), y: this.center.y + this.radius * Math.sin(this.initialAngle) },
      velocity: { x: -this.v * Math.sin(this.initialAngle), y: this.v * Math.cos(this.initialAngle) }, // 切向速度
      acceleration: { x: 0, y: 0 }, // 瞬时加速度向心，但我们计算位置用公式
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'cyan'
    }];
    
    this.trail = [];
    this.time = 0;
    this.isEnded = false;
  }
  
  update(dt) {
    if (this.isEnded) return;
    
    const obj = this.objects[0];
    
    // 匀速圆周: 角度 θ = ω t + θ0
    const theta = this.omega * this.time + this.initialAngle;
    
    // 位置
    obj.position.x = this.center.x + this.radius * Math.cos(theta);
    obj.position.y = this.center.y + this.radius * Math.sin(theta);
    
    // 速度 (切向)
    obj.velocity.x = -this.v * Math.sin(theta);
    obj.velocity.y = this.v * Math.cos(theta);
    
    // 加速度 (向心, 方向向圆心)
    const ax = - (this.v**2 / this.radius) * Math.cos(theta);
    const ay = - (this.v**2 / this.radius) * Math.sin(theta);
    obj.acceleration = { x: ax, y: ay };
    
    // 记录轨迹
    if (this.time % 0.05 < dt) { // 更密集轨迹以显示圆
      this.trail.push({ x: obj.position.x, y: obj.position.y });
    }
    
    // 如果有 duration, 结束
    if (this.duration && this.time >= this.duration) {
      this.isEnded = true;
    }
    
    this.time += dt;
  }
  
  draw() {
  super.draw();
  // 绘制圆心
  this.ctx.fillStyle = 'gray';
  this.ctx.beginPath();
  this.ctx.arc(this.toCanvasX(this.center.x), this.toCanvasY(this.center.y), 5, 0, 2 * Math.PI);
  this.ctx.fill();
  
  if (this.config.showVelocityVectors) {
    this.drawVelocities();  // 使用重写的速度绘制
  }
  
  if (this.config.showForceDiagram) {
    this.drawForces();
  }
}
  
  drawVelocities() {
  const obj = this.objects[0];
  if (obj.velocity) {
    // 绘制切向速度 v_t（方向为 velocity.x/y，大小 v）
    this.drawVector(
      obj.position.x,
      obj.position.y,
      obj.velocity.x,
      obj.velocity.y,
      'blue',
      'v_t'  // 标签为切向速度
    );
    
    // 可选：绘制向心加速度 a_c（向圆心，紫色）
    if (obj.acceleration) {
      this.drawVector(
        obj.position.x,
        obj.position.y,
        obj.acceleration.x,
        obj.acceleration.y,
        'purple',
        'a_c'
      );
    }
  }
}

  drawForces() {
    const obj = this.objects[0];
    const theta = Math.atan2(obj.position.y - this.center.y, obj.position.x - this.center.x);
    
    // 向心力 Fc (向圆心)
    const fcX = -this.centripetal * Math.cos(theta);
    const fcY = -this.centripetal * Math.sin(theta);
    this.drawVector(obj.position.x, obj.position.y, fcX, fcY, 'purple', 'Fc');
    
    // 摩擦力 f (向圆心, 提供向心力)
    this.drawVector(obj.position.x, obj.position.y, fcX, fcY, 'red', 'f'); // 同向 Fc
    
    // 支撑力 Fn (向上, 如果垂直力平衡)
    this.drawVector(obj.position.x, obj.position.y, 0, this.Fn, 'green', 'Fn');
    
    // 重力 G (向下)
    const gForce = this.mass * this.g;
    this.drawVector(obj.position.x, obj.position.y, 0, -gForce, 'orange', 'G');
  }
  
  getPhysicsValues() {
    const obj = this.objects[0] || {};
    const v = this.v.toFixed(2);
    const omega = this.omega.toFixed(2);
    const centripetal = this.centripetal.toFixed(2);
    const gForce = (this.g * this.mass).toFixed(2);
    const friction = Math.min(this.centripetal, this.f_max).toFixed(2);
    const normal = this.Fn.toFixed(2);
    return { v, omega, centripetal, gForce, friction, normal };
  }
}