class FreeFall extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.h0 = params.height || 20;  // 初始高度 m
    this.g = params.g || 9.8;       // 重力加速度
    this.mass = params.mass || 1;   // 质量 kg
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: 5, y: this.h0 },
      velocity: { x: 0, y: 0 },
      acceleration: { x: 0, y: -this.g },
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'red'
    }];
    
    this.trail = [];
    this.time = 0;
  }
  
  update(dt) {
    const obj = this.objects[0];
    
    // 更新速度
    obj.velocity.y += obj.acceleration.y * dt;
    
    // 更新位置
    obj.position.y += obj.velocity.y * dt;
    
    // 记录轨迹
    if (this.time % 0.1 < dt) { // 每0.1秒记录一次
      this.trail.push({
        x: obj.position.x,
        y: obj.position.y
      });
    }
    
    // 落地检测
    if (obj.position.y <= 0) {
      obj.position.y = 0;
      obj.velocity.y = -obj.velocity.y * 0.8; // 反弹（能量损失20%）
    }
  }
}

// 测试代码
const canvas = document.getElementById('test');
const anim = new FreeFall(canvas, {
  height: 20,
  g: 9.8,
  mass: 1
});

anim.play();

// 添加控制
document.getElementById('pause-btn').onclick = () => anim.pause();
document.getElementById('play-btn').onclick = () => anim.play();
document.getElementById('reset-btn').onclick = () => anim.reset();