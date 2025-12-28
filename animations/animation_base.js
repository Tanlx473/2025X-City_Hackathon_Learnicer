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
      showVelocityVectors: true,  // 修改：新增 config for velocity vectors
      showForceDiagram: false,    // 修改：新增 config for force diagram
      showVelocity: true,         // 旧的，保留兼容
      showForce: false            // 旧的，保留兼容
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

    this.isEnded = false;  // 运动结束标志
    
    // 边界padding
    this.boundaryPadding = 50;

    this.config.dimension = config.dimension || '2D';
  }
  
  // 子类必须实现
  init() {
    throw new Error('子类必须实现 init() 方法');
  }
  
  // 子类必须实现
  update(dt) {
    throw new Error('子类必须实现 update() 方法');
  }
  
  calcDynamicScale() {
    // 子类需设置 this.maxRangeX, this.maxRangeY (如射程和高度)
    if (this.maxRangeX && this.maxRangeY) {
      const padding = this.boundaryPadding;
      this.config.scale = Math.min(
        (this.canvas.width - padding * 2) / this.maxRangeX,
        (this.canvas.height - padding * 2) / this.maxRangeY
      );
    }
  }

  // 检查边界
  checkBoundary() {
    for (let obj of this.objects) {
      const x = this.toCanvasX(obj.position.x);
      const y = this.toCanvasY(obj.position.y);
      const radius = obj.radius || 0;
      
      // 检查是否触碰边界
      if (x - radius < 0 || x + radius > this.canvas.width ||
          y - radius < 0 || y + radius > this.canvas.height) {
        this.isEnded = true;
        return true;
      }
    }
    return false;
  }

  // 通用绘制方法
  draw() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    if (this.config.showGrid) {
      this.drawGrid();
    }
    
    this.drawCoordinates();
    this.drawObjects();
    
    if (this.config.showVelocityVectors) {  // 修改：使用新 config
      this.drawVelocities();
    }
    
    if (this.config.showForceDiagram) {  // 修改：使用新 config
      this.drawForces();
    }
    
    this.drawTrail();
    // 修改：移除 drawInfo() 以简化，只保留必要
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
  this.ctx.strokeStyle = '#333';
  this.ctx.lineWidth = 2;
  
  if (this.config.dimension === '1D') {
    // 只画 x 轴（水平放置在画布中部）
    const yPos = this.canvas.height / 2;
    this.ctx.beginPath();
    this.ctx.moveTo(this.boundaryPadding, yPos);
    this.ctx.lineTo(this.canvas.width - 20, yPos);
    this.ctx.stroke();
    
    // 标注
    this.ctx.fillStyle = '#333';
    this.ctx.font = '14px SimHei';
    this.ctx.fillText('x', this.canvas.width - 15, yPos + 20);
    this.ctx.fillText('O', this.boundaryPadding - 20, yPos + 20);
  } else {
    // 原有 xy 轴代码
    // X轴
    this.ctx.beginPath();
    this.ctx.moveTo(this.boundaryPadding, this.canvas.height - this.boundaryPadding);
    this.ctx.lineTo(this.canvas.width - 20, this.canvas.height - this.boundaryPadding);
    this.ctx.stroke();
    
    // Y轴
    this.ctx.beginPath();
    this.ctx.moveTo(this.boundaryPadding, this.canvas.height - this.boundaryPadding);
    this.ctx.lineTo(this.boundaryPadding, 20);
    this.ctx.stroke();
    
    // 标注
    this.ctx.fillStyle = '#333';
    this.ctx.font = '14px SimHei';
    this.ctx.fillText('x', this.canvas.width - 15, this.canvas.height - this.boundaryPadding + 20);
    this.ctx.fillText('y', this.boundaryPadding - 20, 15);
    this.ctx.fillText('O', this.boundaryPadding - 20, this.canvas.height - this.boundaryPadding + 20);
  }
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
        // 修改：绘制水平分量 v1 (vx)
        this.drawVector(
          obj.position.x,
          obj.position.y,
          obj.velocity.x,
          0,
          'green',
          'v₁'  // 简化标签为 v1
        );
        
        // 绘制竖直分量 v2 (vy)
        this.drawVector(
          obj.position.x,
          obj.position.y,
          0,
          obj.velocity.y,
          'orange',
          'v₂'  // 简化标签为 v2
        );
        
        // 绘制合速度 v3 (v)
        this.drawVector(
          obj.position.x,
          obj.position.y,
          obj.velocity.x,
          obj.velocity.y,
          'blue',
          'v₃'  // 简化标签为 v3
        );
      }
    });
  }
  
  drawForces() {
    this.objects.forEach(obj => {
      // 修改：假设主要力是重力 G = mg，绘制重力向量
      const gravityForce = (this.g || 0) * (obj.mass || 0);  // 修改：处理无 g 情况，如匀速 g=0
      this.drawVector(
        obj.position.x,
        obj.position.y,
        0,
        -gravityForce,  // 向下
        'red',
        'G'  // 简化标签为 G
      );
      
      // 如果有其他力，添加 F1, F2 等（示例：如果有加速度相关力）
      if (obj.acceleration && obj.acceleration.x !== 0) {
        this.drawVector(
          obj.position.x,
          obj.position.y,
          obj.acceleration.x * obj.mass,  // F = ma
          0,
          'purple',
          'F₁'
        );
      }
      // 类似添加 F2, F3 如果需要
    });
  }
  
  drawVector(x, y, vx, vy, color, label) {
    const startX = this.toCanvasX(x);
    const startY = this.toCanvasY(y);
    const scale = this.config.scale * 0.1; // 向量缩放
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
    
    // 修改：简化标签，只显示 label（如 'v₁'），不显示数值（数值移到面板）
    this.ctx.font = '12px SimHei';
    this.ctx.fillText(label, endX+5, endY-5);
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
  
  // 修改：移除 drawInfo()，因为需求简化
  
  // 新增：获取实时物理量，用于面板
  getPhysicsValues() {
    const obj = this.objects[0] || {};
    const v = obj.velocity ? Math.sqrt(obj.velocity.x**2 + obj.velocity.y**2).toFixed(2) : 'N/A';
    const vx = obj.velocity ? obj.velocity.x.toFixed(2) : 'N/A';
    const vy = obj.velocity ? obj.velocity.y.toFixed(2) : 'N/A';
    const gForce = ((this.g || 0) * (obj.mass || 0)).toFixed(2);  // 修改：处理无 g，如匀速为0
    // 如果有其他力，添加
    return { v, vx, vy, gForce };
  }
  
  // 坐标转换
  toCanvasX(physicsX) {
    return physicsX * this.config.scale + this.boundaryPadding;
  }
  
  toCanvasY(physicsY) {
    return this.canvas.height - physicsY * this.config.scale - this.boundaryPadding;
  }
  
  // 播放控制
  play() {
    if (!this.isPlaying || this.isPaused) {
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
    this.isEnded = false;
    this.isPlaying = false;
    this.isPaused = false;
    this.init();
    this.draw();
  }
  
  loop() {
    if (this.isPaused) return;
    
    // 检查边界
    if (this.checkBoundary()) {
      this.pause();
      this.draw();
      return;
    }
    
    // 更新和绘制
    this.update(this.dt);
    this.draw();
    
    // 新增：更新物理面板
    updatePhysicsPanel(this);
    
    // 只有在运动未结束时才增加时间
    if (!this.isEnded) {
      this.time += this.dt;
    } else {
      this.pause();
      return;
    }
    
    this.animationId = requestAnimationFrame(() => this.loop());
  }
}