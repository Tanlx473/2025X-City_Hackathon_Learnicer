// simulation_api.js
// 模拟 API 返回函数
function simulateApiResponse(problemDescription) {
  // 基于描述模拟返回（实际替换为 curl 或 fetch API）
  let response = {
    animation_instructions: {
      type: '',
    },
    parameters: {},
    solution_steps: []
  };
  
  return response;
}

// 选择动画并注入参数
function loadAnimationFromApi(canvas, apiResponse) {
  const params = apiResponse.parameters;
  const subType = apiResponse.animation_instructions.type || apiResponse.parameters.motion_type;
  const showVelocity = apiResponse.solution_steps.some(step => 
    step.title && step.title.includes('速度')
  );
  const showAcceleration = apiResponse.solution_steps.some(step => 
    step.title && step.title.includes('加速度')
  );
  
  let AnimationClass;
  switch (subType) {
    case 'free_fall':
      AnimationClass = FreeFall;
      params.showVelocity = showVelocity;
      params.showAcceleration = showAcceleration;
      break;
    case 'projectile_motion':
    case 'projectile':
      AnimationClass = ProjectileMotion;
      params.showVelocity = showVelocity;
      params.showAcceleration = showAcceleration;
      break;
    case 'vertical_throw':
      AnimationClass = VerticalThrow;
      params.showVelocity = showVelocity;
      params.showAcceleration = showAcceleration;
      break;
    case 'uniform':
      AnimationClass = Uniform;
      params.showVelocity = showVelocity;
      params.showAcceleration = showAcceleration;
      break;
    case 'uniform_acceleration':
      return new UniformAcceleration(canvas, params);
    
    case 'uniform_circular':
      return new UniformCircular(canvas, params);
    default:
      throw new Error('未知类型: ' + subType);
  }
  
  return new AnimationClass(canvas, params);
}

// 竖直上抛类（如果需要）
class VerticalThrow extends AnimationBase {
  constructor(canvas, params) {
    super(canvas);
    this.v0 = params.v0;
    this.h0 = params.h0 || 0;
    this.g = params.g || 9.8;
    this.mass = params.mass || 1;
    this.showVelocity = params.showVelocity || true;
    this.showAcceleration = params.showAcceleration || false;
    
    this.init();
  }
  
  init() {
    this.objects = [{
      position: { x: 5, y: this.h0 },
      velocity: { x: 0, y: this.v0 },
      acceleration: { x: 0, y: -this.g },
      shape: 'circle',
      radius: 10,
      mass: this.mass,
      color: 'blue'
    }];
    
    this.trail = [];
    this.time = 0;
    this.isEnded = false;
  }
  
  update(dt) {
    if (this.isEnded) return;
    
    const obj = this.objects[0];
    
    // 更新速度和位置
    obj.velocity.y = this.v0 - this.g * this.time;
    obj.position.y = this.h0 + this.v0 * this.time - 0.5 * this.g * this.time**2;
    
    // 记录轨迹
    if (this.time % 0.1 < dt) {
      this.trail.push({ x: obj.position.x, y: obj.position.y });
    }
    
    // 落地检测
    if (obj.position.y <= 0) {
      obj.position.y = 0;
      obj.velocity.y = 0;
      this.isEnded = true;
    }
  }
  
  draw() {
    super.draw();
    if (this.showAcceleration) {
      this.drawVector(this.objects[0].position.x, this.objects[0].position.y, 0, this.objects[0].acceleration.y, 'green', 'a');
    }
  }
}