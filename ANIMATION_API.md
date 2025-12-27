# Canvas 动画模块 API 文档

## 📌 合并说明

本仓库的 Canvas 动画模块已完成合并审计，现在采用**统一架构**：

- **核心实现**：`animations/` 文件夹（C 同学的完整物理引擎）
- **兼容适配层**：`static/animation.js`（将 A 同学的旧接口映射到新实现）
- **对外暴露接口**：`window.AnimationEngine`（保持向后兼容）

---

## 🎯 对外接口（统一入口）

### 1. 初始化

```javascript
const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);
```

**参数**：
- `canvas` (HTMLCanvasElement) - 必需，Canvas DOM 元素

---

### 2. 加载动画指令

```javascript
engine.loadInstructions(data);
```

**支持的数据格式**：

#### 格式 A：旧格式（自动转换）
```javascript
{
  type: 'projectile',        // 运动类型：'projectile' | 'free_fall'
  initial_speed: 20,         // 初速度 (m/s)
  angle: 45,                 // 发射角度 (度)
  gravity: 9.8,              // 重力加速度 (m/s²)
  initial_x: 0,              // 初始 x 坐标 (m)
  initial_y: 0,              // 初始 y 坐标 (m)
  scale: 20,                 // 缩放比例 (像素/米)
  duration: 5                // 动画时长 (秒)
}
```

#### 格式 B：新格式（推荐）
```javascript
{
  sub_type: 'projectile_motion',   // 'projectile_motion' | 'free_fall'
  parameters: {
    v0: 20,                        // 初速度 (m/s)
    angle: 45,                     // 发射角度 (度)
    g: 9.8,                        // 重力加速度 (m/s²)
    h0: 0,                         // 初始高度 (m)
    mass: 1                        // 质量 (kg)
  },
  solution_steps: [                // 可选：解题步骤（用于步骤联动）
    {
      step: 1,
      description: "分解初速度",
      formula: "vₓ = v₀·cos45° = 14.14 m/s",
      animation_time: [0, 1]       // [开始时间, 结束时间] (秒)
    }
  ]
}
```

**类型映射规则**：
| 旧格式 `type` | 新格式 `sub_type` | 说明 |
|--------------|------------------|------|
| `projectile` | `projectile_motion` | 抛体运动 |
| `free_fall` | `free_fall` | 自由落体 |

**字段映射规则**：
| 旧字段 | 新字段 | 备注 |
|--------|--------|------|
| `initial_speed` | `v0` | 初速度 |
| `gravity` | `g` | 重力加速度 |
| `initial_y` | `h0` | 初始高度 |
| `angle` | `angle` | 保持不变 |

---

### 3. 控制方法

#### 播放动画
```javascript
engine.play();
```

#### 暂停动画
```javascript
engine.pause();
```

#### 重播动画
```javascript
engine.reset();  // 重置到初始状态
engine.play();   // 重新播放
```

#### 销毁引擎
```javascript
engine.destroy();  // 停止动画并清理资源
```

---

## 🔧 使用示例

### 示例 1：基础抛体运动（旧格式）
```javascript
const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);

engine.loadInstructions({
  type: 'projectile',
  initial_speed: 20,
  angle: 45,
  gravity: 9.8,
  scale: 20
});

engine.play();
```

### 示例 2：自由落体（新格式）
```javascript
const engine = new AnimationEngine(canvas);

engine.loadInstructions({
  sub_type: 'free_fall',
  parameters: {
    h0: 20,      // 初始高度 20 米
    g: 9.8,      // 地球重力
    mass: 1      // 1 千克物体
  }
});

engine.play();
```

### 示例 3：完整流程（从后端获取数据）
```javascript
fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => {
  const engine = new AnimationEngine(canvas);

  // 后端返回的 animation_instructions 自动适配
  engine.loadInstructions(data.animation_instructions);

  // 绑定控制按钮
  document.getElementById('playBtn').onclick = () => engine.play();
  document.getElementById('pauseBtn').onclick = () => engine.pause();
  document.getElementById('replayBtn').onclick = () => {
    engine.reset();
    engine.play();
  };
});
```

---

## 📦 模块架构

### 文件加载顺序（templates/index.html）
```html
<!-- 1. 核心基类 -->
<script src="/animations/animation_base.js"></script>

<!-- 2. 具体实现类 -->
<script src="/animations/free_fall.js"></script>
<script src="/animations/projectile_motion.js"></script>

<!-- 3. 统一可视化接口 -->
<script src="/animations/physics_visualizer.js"></script>

<!-- 4. 兼容适配层（暴露 AnimationEngine） -->
<script src="/static/animation.js"></script>

<!-- 5. 前端业务逻辑 -->
<script src="/static/main.js"></script>
```

### 内部调用链
```
前端代码 (main.js)
    ↓ 调用
AnimationEngine (static/animation.js) - 兼容适配层
    ↓ 映射到
PhysicsVisualizer (animations/physics_visualizer.js) - 统一接口
    ↓ 分发到
ProjectileMotion / FreeFall (animations/*.js) - 具体实现
    ↓ 继承自
AnimationBase (animations/animation_base.js) - 基类
```

---

## ⚠️ 重要约束

1. **必须按顺序加载脚本**：animations/ 模块必须在 static/animation.js 之前加载
2. **Canvas 必须存在**：在调用 `new AnimationEngine(canvas)` 前确保 Canvas 元素已渲染
3. **数据格式兼容性**：
   - 旧格式会自动转换为新格式
   - 如果后端已升级为新格式，直接传入即可
   - 数组格式会使用默认示例（用于占位）

---

## 🧪 调试技巧

### 查看格式转换过程
打开浏览器控制台，调用 `loadInstructions()` 后会输出：
```
[兼容层] 旧格式 → 新格式转换: {
  原始数据: {...},
  转换后: {...}
}
```

### 检查当前动画状态
```javascript
console.log(engine.isPlaying);  // true/false
console.log(engine.visualizer.currentAnimation);  // 当前动画实例
```

---

## 🎓 迁移指南

### 从旧版本（纯 A 同学版本）迁移
✅ **无需修改前端代码**，API 完全兼容！

如果之前使用：
```javascript
const engine = new AnimationEngine(canvas);
engine.loadInstructions(data);
engine.play();
```

现在仍然可以正常工作，但内部已切换到 animations/ 的实现。

### 升级到新格式（可选）
建议后端逐步升级为新格式（`sub_type` + `parameters`），获得更丰富的功能：
- 关键点标记
- 解题步骤联动（`playStep(stepIndex)`）
- 结果面板展示

---

## 📞 问题反馈

如果遇到兼容性问题或格式转换错误，请检查：
1. 浏览器控制台的错误信息
2. `[兼容层]` 转换日志
3. 确认 Canvas 尺寸和 ID 正确