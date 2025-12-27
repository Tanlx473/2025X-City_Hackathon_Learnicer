/**
 * 动画基类
 */
class AnimationBase {
  constructor(canvas, config = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.config = Object.assign({
      scale: 50,           // 像素/米
      fps: 60,
      showGrid: true,
      showVelocity: true,
      showForce: false
    }, config);
    
    this.time = 0;
    this.dt = 1 / this.config.fps;
    this.isPlaying = false;
    this.isPaused = false;
    this.animationId = null;
    
    this.objects = [];      // 物体数组
    this.forces = [];       // 力数组
    this.constraints = [];  // 约束数组
    this.trail = [];        // 轨迹点
  }
  
  // 子类必须实现
  init() {
    throw new Error('子类必须实现 init() 方法');
  }
  
  // 子类必须实现
  update(dt) {
    throw new Error('子类必须实现 update() 方法');
  }
  
  // 通用绘制方法
  draw() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    if (this.config.showGrid) {
      this.drawGrid();
    }
    
    this.drawCoordinates();
    this.drawObjects();
    
    if (this.config.showVelocity) {
      this.drawVelocities();
    }
    
    if (this.config.showForce) {
      this.drawForces();
    }
    
    this.drawTrail();
    this.drawInfo();
  }
  
  drawGrid() {
    const { scale } = this.config;
    this.ctx.strokeStyle = '#e0e0e0';
    this.ctx.lineWidth = 0.5;
    
    // 垂直线
    for (let x = 0; x < this.canvas.width; x += scale) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.canvas.height);
      this.ctx.stroke();
    }
    
    // 水平线
    for (let y = 0; y < this.canvas.height; y += scale) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.canvas.width, y);
      this.ctx.stroke();
    }
  }
  
  drawCoordinates() {
    // 实现坐标系绘制（复用上面的代码）
    // ...
  }
  
  drawObjects() {
    this.objects.forEach(obj => {
      const x = this.toCanvasX(obj.position.x);
      const y = this.toCanvasY(obj.position.y);
      
      this.ctx.save();
      this.ctx.translate(x, y);
      this.ctx.rotate(obj.angle || 0);
      
      // 根据类型绘制
      if (obj.shape === 'circle') {
        this.ctx.fillStyle = obj.color || 'red';
        this.ctx.beginPath();
        this.ctx.arc(0, 0, obj.radius, 0, 2*Math.PI);
        this.ctx.fill();
      } else if (obj.shape === 'rectangle') {
        this.ctx.fillStyle = obj.color || 'blue';
        this.ctx.fillRect(-obj.width/2, -obj.height/2, obj.width, obj.height);
      }
      
      // 绘制质量标注
      if (obj.mass) {
        this.ctx.fillStyle = 'black';
        this.ctx.font = '12px SimHei';
        this.ctx.fillText(`m=${obj.mass}kg`, 10, -10);
      }
      
      this.ctx.restore();
    });
  }
  
  drawVelocities() {
    this.objects.forEach(obj => {
      if (obj.velocity) {
        this.drawVector(
          obj.position.x,
          obj.position.y,
          obj.velocity.x,
          obj.velocity.y,
          'blue',
          'v'
        );
      }
    });
  }
  
  drawVector(x, y, vx, vy, color, label) {
    const startX = this.toCanvasX(x);
    const startY = this.toCanvasY(y);
    const scale = this.config.scale * 0.1; // 速度向量缩放
    const endX = startX + vx * scale;
    const endY = startY - vy * scale;
    
    // 画箭头
    this.ctx.strokeStyle = color;
    this.ctx.fillStyle = color;
    this.ctx.lineWidth = 2;
    
    this.ctx.beginPath();
    this.ctx.moveTo(startX, startY);
    this.ctx.lineTo(endX, endY);
    this.ctx.stroke();
    
    // 箭头头部
    const angle = Math.atan2(endY - startY, endX - startX);
    this.ctx.beginPath();
    this.ctx.moveTo(endX, endY);
    this.ctx.lineTo(endX - 10*Math.cos(angle-Math.PI/6), endY - 10*Math.sin(angle-Math.PI/6));
    this.ctx.lineTo(endX - 10*Math.cos(angle+Math.PI/6), endY - 10*Math.sin(angle+Math.PI/6));
    this.ctx.closePath();
    this.ctx.fill();
    
    // 标签
    const magnitude = Math.sqrt(vx*vx + vy*vy);
    this.ctx.font = '12px SimHei';
    this.ctx.fillText(`${label}=${magnitude.toFixed(2)}m/s`, endX+5, endY-5);
  }
  
  drawTrail() {
    if (this.trail.length < 2) return;
    
    this.ctx.strokeStyle = 'rgba(255, 0, 0, 0.3)';
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([5, 5]);
    
    this.ctx.beginPath();
    this.trail.forEach((point, i) => {
      const x = this.toCanvasX(point.x);
      const y = this.toCanvasY(point.y);
      if (i === 0) this.ctx.moveTo(x, y);
      else this.ctx.lineTo(x, y);
    });
    this.ctx.stroke();
    this.ctx.setLineDash([]);
  }
  
  drawInfo() {
    this.ctx.fillStyle = 'black';
    this.ctx.font = '14px SimHei';
    this.ctx.fillText(`时间: ${this.time.toFixed(2)} s`, 10, 20);
  }
  
  // 坐标转换
  toCanvasX(physicsX) {
    return physicsX * this.config.scale + 50;
  }
  
  toCanvasY(physicsY) {
    return this.canvas.height - physicsY * this.config.scale - 50;
  }
  
  // 播放控制
  play() {
    if (!this.isPlaying) {
      this.isPlaying = true;
      this.isPaused = false;
      this.loop();
    }
  }
  
  pause() {
    this.isPaused = true;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }
  
  reset() {
    this.pause();
    this.time = 0;
    this.trail = [];
    this.init();
    this.draw();
  }
  
  loop() {
    if (this.isPaused) return;
    
    this.update(this.dt);
    this.draw();
    this.time += this.dt;
    
    this.animationId = requestAnimationFrame(() => this.loop());
  }
}