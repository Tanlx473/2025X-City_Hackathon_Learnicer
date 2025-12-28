class UniformAcceleration extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.F = params.F;        // 拉力 F
    this.mu = params.mu;      // 摩擦系数 μ
    this.mass = params.mass;  // 质量 m
    this.g = params.g || 9.8; // 重力加速度
    this.x0 = params.x0 || 0; // 初始 x
    this.v0 = params.v0 || 0; // 初速度
    this.duration = params.duration || 10; // 总时长
    this.Fn = this.mass * this.g; // 支撑力 Fn = mg (假设水平地面)
    this.f = this.mu * this.Fn;   // 摩擦力 f = μ * Fn
    this.a = (this.F - this.f) / this.mass; // 加速度 a = (F - f)/m
    this.showVelocity = params.showVelocity || true;
    this.showAcceleration = params.showAcceleration || true;
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: this.x0, y: 0 }, // 只在一维 x 上运动, y=0
      velocity: { x: this.v0, y: 0 },
      acceleration: { x: this.a, y: 0 },
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'purple'
    }];
    
    this.trail = [];
    this.time = 0;
    this.isEnded = false;
  }
  
  update(dt) {
    if (this.isEnded) return;
    
    const obj = this.objects[0];
    
    // 匀加速: v = v0 + a t
    obj.velocity.x = this.v0 + this.a * this.time;
    
    // 位置 x = x0 + v0 t + 0.5 a t^2
    obj.position.x = this.x0 + this.v0 * this.time + 0.5 * this.a * this.time**2;
    obj.position.y = 0;
    
    // 记录轨迹
    if (this.time % 0.1 < dt) {
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
    if (this.config.showForceDiagram) {
      this.drawForces();
    }
  }
  
  drawForces() {
    const obj = this.objects[0];
    // 绘制拉力 F (向前)
    this.drawVector(obj.position.x, obj.position.y, this.F, 0, 'blue', 'F');
    
    // 绘制摩擦力 f (向后)
    this.drawVector(obj.position.x, obj.position.y, -this.f, 0, 'red', 'f');
    
    // 绘制支撑力 Fn (向上)
    this.drawVector(obj.position.x, obj.position.y, 0, this.Fn, 'green', 'Fn');
    
    // 重力 G (向下)
    const gForce = this.mass * this.g;
    this.drawVector(obj.position.x, obj.position.y, 0, -gForce, 'orange', 'G');
  }
  
  getPhysicsValues() {
    const obj = this.objects[0] || {};
    const v = obj.velocity ? Math.sqrt(obj.velocity.x**2 + obj.velocity.y**2).toFixed(2) : 'N/A';
    const vx = obj.velocity ? obj.velocity.x.toFixed(2) : 'N/A';
    const vy = obj.velocity ? obj.velocity.y.toFixed(2) : 'N/A';
    const gForce = (this.g * this.mass).toFixed(2);
    const friction = this.f.toFixed(2);
    const tension = this.F.toFixed(2);
    const normal = this.Fn.toFixed(2);
    return { v, vx, vy, gForce, friction, tension, normal };
  }
}