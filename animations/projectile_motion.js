class ProjectileMotion extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.v0 = params.v0 || 20;
    this.angle = params.angle * Math.PI / 180;
    this.h0 = params.h0 || 0;
    this.g = params.g || 9.8;
    this.mass = params.mass || 1;
    
    // 计算初速度分量
    this.vx0 = this.v0 * Math.cos(this.angle);
    this.vy0 = this.v0 * Math.sin(this.angle);
    
    // 计算关键点
    this.calcKeyPoints();
    this.init();
  }
  
  calcKeyPoints() {
    // 最高点
    this.t_max = this.vy0 / this.g;
    this.h_max = this.h0 + this.vy0**2 / (2*this.g);
    this.x_max = this.vx0 * this.t_max;
    
    // 落地点
    const delta = this.vy0**2 + 2*this.g*this.h0;
    this.t_land = (this.vy0 + Math.sqrt(delta)) / this.g;
    this.range = this.vx0 * this.t_land;
    
    console.log('关键点计算结果:', {
      最高点时间: this.t_max,
      最大高度: this.h_max,
      落地时间: this.t_land,
      水平射程: this.range
    });
  }
  
  init() {
    this.objects = [{
      position: { x: 0, y: this.h0 },
      velocity: { x: this.vx0, y: this.vy0 },
      acceleration: { x: 0, y: -this.g },
      shape: 'circle',
      radius: 8,
      mass: this.mass,
      color: 'red'
    }];
    
    this.trail = [];
    this.keyPoints = [];
    this.time = 0;
  }
  
  update(dt) {
    const obj = this.objects[0];
    
    // 匀变速运动公式
    obj.velocity.x = this.vx0;
    obj.velocity.y = this.vy0 - this.g * this.time;
    
    obj.position.x = this.vx0 * this.time;
    obj.position.y = this.h0 + this.vy0 * this.time - 0.5 * this.g * this.time**2;
    
    // 记录轨迹
    this.trail.push({
      x: obj.position.x,
      y: obj.position.y
    });
    
    // 标记关键点
    if (Math.abs(this.time - this.t_max) < dt && this.keyPoints.length === 0) {
      this.keyPoints.push({
        x: obj.position.x,
        y: obj.position.y,
        label: '最高点',
        data: {
          time: this.time,
          height: obj.position.y,
          velocity: Math.sqrt(obj.velocity.x**2 + obj.velocity.y**2)
        }
      });
    }
    
    // 结束条件
    if (obj.position.y < 0 || this.time > this.t_land + 0.1) {
      this.pause();
      this.showResults();
    }
  }
  
  draw() {
    super.draw();
    this.drawKeyPoints();
    this.drawComponents(); // 绘制速度分量
  }
  
  drawKeyPoints() {
    this.keyPoints.forEach(point => {
      const x = this.toCanvasX(point.x);
      const y = this.toCanvasY(point.y);
      
      // 画圆圈
      this.ctx.strokeStyle = 'green';
      this.ctx.lineWidth = 2;
      this.ctx.setLineDash([5, 5]);
      this.ctx.beginPath();
      this.ctx.arc(x, y, 20, 0, 2*Math.PI);
      this.ctx.stroke();
      this.ctx.setLineDash([]);
      
      // 标签
      this.ctx.fillStyle = 'green';
      this.ctx.font = 'bold 14px SimHei';
      this.ctx.fillText(point.label, x + 25, y - 10);
      
      // 数据
      this.ctx.font = '12px SimHei';
      this.ctx.fillText(`t=${point.data.time.toFixed(2)}s`, x + 25, y + 10);
      this.ctx.fillText(`h=${point.data.height.toFixed(2)}m`, x + 25, y + 25);
    });
  }
  
  drawComponents() {
    const obj = this.objects[0];
    const x = this.toCanvasX(obj.position.x);
    const y = this.toCanvasY(obj.position.y);
    
    // 绘制vx（水平分量）
    this.drawVector(
      obj.position.x,
      obj.position.y,
      obj.velocity.x,
      0,
      'green',
      'vₓ'
    );
    
    // 绘制vy（竖直分量）
    this.drawVector(
      obj.position.x,
      obj.position.y,
      0,
      obj.velocity.y,
      'orange',
      'vᵧ'
    );
  }
  
  showResults() {
    // 在Canvas上绘制结果面板
    const x = this.canvas.width - 250;
    const y = 50;
    
    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
    this.ctx.strokeStyle = '#333';
    this.ctx.lineWidth = 2;
    this.ctx.fillRect(x, y, 230, 180);
    this.ctx.strokeRect(x, y, 230, 180);
    
    this.ctx.fillStyle = 'black';
    this.ctx.font = 'bold 16px SimHei';
    this.ctx.fillText('计算结果', x + 80, y + 30);
    
    this.ctx.font = '14px SimHei';
    const results = [
      `初速度：${this.v0} m/s`,
      `发射角：${(this.angle * 180 / Math.PI).toFixed(1)}°`,
      `最大高度：${this.h_max.toFixed(2)} m`,
      `最高点时间：${this.t_max.toFixed(2)} s`,
      `飞行时间：${this.t_land.toFixed(2)} s`,
      `水平射程：${this.range.toFixed(2)} m`
    ];
    
    results.forEach((text, i) => {
      this.ctx.fillText(text, x + 15, y + 60 + i * 20);
    });
  }
}