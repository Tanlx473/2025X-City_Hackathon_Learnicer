/**
 * 物理可视化主模块
 * 对接前后端的统一接口
 */
class PhysicsVisualizer {
  constructor(canvasOrId, config = {}) {
    // 支持传入 Canvas 元素或 ID 字符串
    if (typeof canvasOrId === 'string') {
      this.canvas = document.getElementById(canvasOrId);
      if (!this.canvas) {
        throw new Error(`找不到Canvas元素: ${canvasOrId}`);
      }
    } else if (canvasOrId instanceof HTMLCanvasElement) {
      this.canvas = canvasOrId;
    } else {
      throw new Error('参数必须是 Canvas 元素或 ID 字符串');
    }

    this.config = config;
    this.currentAnimation = null;
    this.animationData = null;
  }
  
  /**
   * 加载后端返回的数据
   * @param {Object} data - 后端JSON数据
   */
  loadAnimation(data) {
    console.log('接收到动画数据:', data);

    this.animationData = data;
    const params = data.parameters;
    const subType = data.sub_type;

    // 根据题型创建对应的动画对象
    switch(subType) {
      case 'free_fall':
        this.currentAnimation = new FreeFall(this.canvas, params);
        break;

      case 'projectile_motion':
        this.currentAnimation = new ProjectileMotion(this.canvas, params);
        break;

      case 'uniform':
        this.currentAnimation = new Uniform(this.canvas, params);
        break;

      case 'uniform_acceleration':
        this.currentAnimation = new UniformAcceleration(this.canvas, params);
        break;

      case 'uniform_circular':
        this.currentAnimation = new UniformCircular(this.canvas, params);
        break;

      case 'incline_plane':
        this.currentAnimation = new InclinePlaneMotion(this.canvas, params);
        break;

      case 'circular_motion':
        this.currentAnimation = new CircularMotion(this.canvas, params);
        break;

      default:
        console.warn(`未知的动画类型: ${subType}，尝试使用 projectile_motion 作为 fallback`);
        this.currentAnimation = new ProjectileMotion(this.canvas, params);
        break;
    }
    
    // 触发事件通知前端
    this.canvas.dispatchEvent(new CustomEvent('animation:loaded', {
      detail: { data: data }
    }));
    
    return this;
  }
  
  // 暴露控制方法
  play() { 
    if (this.currentAnimation) {
      this.currentAnimation.play(); 
      this.canvas.dispatchEvent(new Event('animation:play'));
    }
  }
  
  pause() { 
    if (this.currentAnimation) {
      this.currentAnimation.pause(); 
      this.canvas.dispatchEvent(new Event('animation:pause'));
    }
  }
  
  reset() { 
    if (this.currentAnimation) {
      this.currentAnimation.reset(); 
      this.canvas.dispatchEvent(new Event('animation:reset'));
    }
  }
  
  playStep(stepIndex) {
    if (!this.animationData || !this.animationData.solution_steps) {
      console.error('没有解题步骤数据');
      return;
    }
    
    const steps = this.animationData.solution_steps;
    if (stepIndex < 0 || stepIndex >= steps.length) {
      console.error('步骤索引越界');
      return;
    }
    
    const step = steps[stepIndex];
    const [start, end] = step.animation_time;
    
    this.currentAnimation.playSegment(start, end);
    
    // 通知前端高亮对应步骤
    this.canvas.dispatchEvent(new CustomEvent('step:active', {
      detail: { stepIndex, step }
    }));
  }
  
  exportFrame() {
    return this.canvas.toDataURL('image/png');
  }
}

// 全局导出
window.PhysicsVisualizer = PhysicsVisualizer;