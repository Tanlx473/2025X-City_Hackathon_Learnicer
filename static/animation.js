/**
 * AnimationEngine - 兼容适配层
 *
 * 职责：将 A 同学的旧接口映射到 animations/ 文件夹的新实现（C 同学版本）
 *
 * 旧接口（保留向后兼容）：
 *   - new AnimationEngine(canvas)
 *   - engine.loadInstructions(data)
 *   - engine.play() / pause() / reset()
 *
 * 新实现（内部使用 PhysicsVisualizer）：
 *   - animations/physics_visualizer.js
 *   - animations/animation_base.js
 *   - animations/projectile_motion.js
 *   - animations/free_fall.js
 */

class AnimationEngine {
  constructor(canvas) {
    if (!canvas) {
      throw new Error('Canvas 元素不存在');
    }
    this.canvas = canvas;

    // 内部使用 PhysicsVisualizer（C 同学的核心引擎）
    this.visualizer = new PhysicsVisualizer(canvas, {});

    // 保留旧接口的状态（用于兼容性）
    this.isPlaying = false;
  }

  /**
   * 数据格式标准化：旧格式 → 新格式
   *
   * 旧格式（A 同学）：
   * {
   *   type: 'projectile',
   *   initial_speed: 16,
   *   angle: 50,
   *   gravity: 9.8,
   *   initial_x: 0,
   *   initial_y: 0,
   *   scale: 22,
   *   duration: 4
   * }
   *
   * 新格式（C 同学）：
   * {
   *   sub_type: 'projectile_motion',
   *   parameters: {
   *     v0: 20,
   *     angle: 45,
   *     g: 9.8,
   *     h0: 0,
   *     mass: 1
   *   },
   *   solution_steps: [...]
   * }
   */
  static normalizePayload(raw) {
    if (!raw) return null;

    // 如果是数组，使用默认抛体运动示例
    if (Array.isArray(raw)) {
      return {
        sub_type: 'projectile_motion',
        parameters: {
          v0: 18,
          angle: 55,
          g: 9.8,
          h0: 0,
          mass: 1
        }
      };
    }

    // 如果已经是新格式（包含 sub_type 和 parameters），直接返回
    if (raw.sub_type && raw.parameters) {
      return raw;
    }

    // 如果嵌套在 animation 字段中
    if (raw.animation) {
      return AnimationEngine.normalizePayload(raw.animation);
    }

    // 旧格式转新格式的映射逻辑
    // 优先使用 motion_type_original，其次使用 type
    const motionType = raw.motion_type_original || raw.type || 'projectile';

    // 提取通用参数
    const v0 = raw.initial_speed !== undefined ? raw.initial_speed : (raw.v0 !== undefined ? raw.v0 : 20);
    const angle = raw.angle !== undefined ? raw.angle : 45;
    const g = raw.gravity !== undefined ? raw.gravity : (raw.g !== undefined ? raw.g : 9.8);
    const h0 = raw.initial_y !== undefined ? raw.initial_y : (raw.y0 !== undefined ? raw.y0 : (raw.h0 !== undefined ? raw.h0 : 0));
    const mass = raw.mass !== undefined ? raw.mass : 1;
    const duration = raw.duration !== undefined ? raw.duration : 10;

    // 映射到 PhysicsVisualizer 支持的类型并构建对应参数
    let subType, parameters;

    if (motionType === 'free_fall') {
      subType = 'free_fall';
      parameters = {
        h0: h0 || 10,  // 自由落体默认高度
        g: g,
        mass: mass,
        bounce: raw.bounce || false,
        bounceLoss: raw.bounceLoss || 0.8
      };
    } else if (motionType === 'uniform') {
      subType = 'uniform';
      // Uniform 需要 vx, vy 而不是 v0, angle
      const angleRad = (angle || 0) * Math.PI / 180;
      parameters = {
        vx: v0 * Math.cos(angleRad),
        vy: v0 * Math.sin(angleRad),
        x0: raw.initial_x !== undefined ? raw.initial_x : 0,
        y0: h0,
        mass: mass,
        duration: duration,
        g: 0  // 匀速运动无重力影响
      };
    } else if (motionType === 'uniform_acceleration') {
      subType = 'uniform_acceleration';
      parameters = {
        F: raw.F !== undefined ? raw.F : 10,  // 拉力
        mu: raw.mu !== undefined ? raw.mu : 0.2,  // 摩擦系数
        mass: mass,
        g: g,
        x0: raw.initial_x !== undefined ? raw.initial_x : 0,
        v0: v0,
        duration: duration
      };
    } else if (motionType === 'uniform_circular') {
      subType = 'uniform_circular';
      parameters = {
        radius: raw.radius !== undefined ? raw.radius : 5,  // 半径
        omega: raw.omega !== undefined ? raw.omega : 1,  // 角速度
        mass: mass,
        mu: raw.mu !== undefined ? raw.mu : 0.5,
        g: g,
        duration: duration
      };
    } else {
      // horizontal_projectile, vertical_throw, projectile 都映射为 projectile_motion
      subType = 'projectile_motion';
      parameters = {
        v0: v0,
        angle: angle,
        g: g,
        h0: h0,
        mass: mass
      };
    }

    return {
      sub_type: subType,
      parameters: parameters
    };
  }

  /**
   * 加载动画指令（旧接口）
   * @param {Object|Array} data - 动画数据（自动转换格式）
   */
  loadInstructions(data) {
    const normalized = AnimationEngine.normalizePayload(data);
    if (!normalized) {
      throw new Error('动画指令为空或格式不支持');
    }

    console.log('[兼容层] 旧格式 → 新格式转换:', {
      原始数据: data,
      转换后: normalized
    });

    // 调用 PhysicsVisualizer.loadAnimation()
    this.visualizer.loadAnimation(normalized);
  }

  /**
   * 播放动画
   */
  play() {
    this.isPlaying = true;
    this.visualizer.play();
  }

  /**
   * 暂停动画
   */
  pause() {
    this.isPlaying = false;
    this.visualizer.pause();
  }

  /**
   * 重置动画
   */
  reset() {
    this.isPlaying = false;
    this.visualizer.reset();
  }

  /**
   * 调整画布尺寸（可选功能）
   */
  resize(width, height) {
    if (width && height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
  }

  /**
   * 销毁动画引擎（可选功能）
   */
  destroy() {
    this.pause();
    if (this.visualizer.currentAnimation) {
      this.visualizer.currentAnimation.pause();
    }
  }
}

// 全局导出（确保兼容性）
if (typeof window !== 'undefined') {
  window.AnimationEngine = AnimationEngine;
}