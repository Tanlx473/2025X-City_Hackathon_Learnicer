# Canvas 动画模块验证指南

## 🧪 本地验证步骤

### 方式 1：使用现有页面测试

1. **启动后端服务**
   ```bash
   cd /Users/jeremytan/Desktop/2025X-City_Hackathon_Learnicer
   python app.py
   ```

2. **打开浏览器访问**
   ```
   http://localhost:5000
   ```

3. **打开浏览器控制台（F12）**
   - 检查是否有脚本加载错误
   - 查看 `[兼容层]` 的转换日志

4. **上传示例图片或使用 Mock 数据**
   - 方式 A：上传真实物理题目图片
   - 方式 B：在控制台手动触发 Mock 动画（见下方）

---

### 方式 2：控制台手动测试

在浏览器控制台（F12）中执行：

#### 测试 1：抛体运动（旧格式）
```javascript
const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);

// 旧格式（自动转换）
engine.loadInstructions({
  type: 'projectile',
  initial_speed: 20,
  angle: 45,
  gravity: 9.8,
  initial_x: 0,
  initial_y: 0,
  scale: 20
});

engine.play();
```

#### 测试 2：自由落体（新格式）
```javascript
const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);

// 新格式
engine.loadInstructions({
  sub_type: 'free_fall',
  parameters: {
    height: 20,  // 初始高度 20 米
    g: 9.8,
    mass: 1
  }
});

engine.play();
```

#### 测试 3：控制按钮验证
```javascript
// 暂停
engine.pause();

// 继续播放
engine.play();

// 重播
engine.reset();
engine.play();
```

---

## 📋 Mock 数据示例

### Mock 1：平抛运动（旧格式）
```json
{
  "type": "projectile",
  "initial_speed": 15,
  "angle": 30,
  "gravity": 9.8,
  "initial_x": 0,
  "initial_y": 5,
  "scale": 22,
  "duration": 3
}
```

**预期结果**：
- 物体从 (0, 5) 位置开始
- 以 30° 角、15 m/s 初速度抛出
- 显示抛物线轨迹
- 显示速度向量（蓝色箭头）
- 约 3 秒后到达地面

---

### Mock 2：斜抛运动（新格式）
```json
{
  "sub_type": "projectile_motion",
  "parameters": {
    "v0": 20,
    "angle": 45,
    "h0": 0,
    "g": 9.8,
    "mass": 1
  },
  "solution_steps": [
    {
      "step": 1,
      "description": "分解初速度",
      "formula": "vₓ = v₀·cos45° = 14.14 m/s, vᵧ = v₀·sin45° = 14.14 m/s",
      "animation_time": [0, 1]
    },
    {
      "step": 2,
      "description": "物体上升阶段",
      "formula": "最高点时 vᵧ = 0",
      "animation_time": [1, 1.44]
    },
    {
      "step": 3,
      "description": "计算最大高度",
      "formula": "h_max = vᵧ²/(2g) = 10.2 m",
      "animation_time": [1.44, 1.5]
    },
    {
      "step": 4,
      "description": "物体下降阶段",
      "formula": "vᵧ = gt",
      "animation_time": [1.5, 2.88]
    },
    {
      "step": 5,
      "description": "计算射程",
      "formula": "R = v₀²·sin(2θ)/g = 40.8 m",
      "animation_time": [2.88, 3]
    }
  ]
}
```

**预期结果**：
- 完整抛体运动轨迹
- 标记最高点（绿色圆圈 + 标签）
- 显示水平和竖直速度分量
- 动画结束时显示计算结果面板

---

### Mock 3：自由落体（新格式）
```json
{
  "sub_type": "free_fall",
  "parameters": {
    "height": 20,
    "g": 9.8,
    "mass": 2
  }
}
```

**预期结果**：
- 物体从 20 米高度自由下落
- 竖直向下加速
- 落地后有反弹效果（能量损失 20%）
- 显示速度向量变化

---

## 🔍 验证检查项

### ✅ 功能验证
- [ ] 动画能正常加载和播放
- [ ] 播放/暂停/重播按钮工作正常
- [ ] 轨迹绘制正确（抛物线/直线）
- [ ] 速度向量显示正确（方向和大小）
- [ ] 网格和坐标系显示正常
- [ ] 物体运动符合物理规律

### ✅ 兼容性验证
- [ ] 旧格式（type: 'projectile'）能自动转换
- [ ] 新格式（sub_type: 'projectile_motion'）直接可用
- [ ] 数组格式使用默认示例
- [ ] 控制台无报错信息
- [ ] `[兼容层]` 日志显示正确转换

### ✅ 视觉验证
- [ ] Canvas 尺寸正确（720×420）
- [ ] 物体颜色正确（红色圆圈）
- [ ] 速度向量颜色正确（蓝色箭头）
- [ ] 轨迹颜色正确（橙色线条）
- [ ] 网格和地面线显示清晰

---

## 🎯 快速验证脚本

### 一键测试所有场景

在浏览器控制台执行以下代码，自动运行所有测试：

```javascript
// 快速验证脚本
(async function runAllTests() {
  const canvas = document.getElementById('animationCanvas');
  if (!canvas) {
    console.error('❌ Canvas 元素未找到！');
    return;
  }

  const tests = [
    {
      name: '测试 1：旧格式平抛运动',
      data: {
        type: 'projectile',
        initial_speed: 15,
        angle: 30,
        gravity: 9.8,
        scale: 20
      }
    },
    {
      name: '测试 2：新格式斜抛运动',
      data: {
        sub_type: 'projectile_motion',
        parameters: { v0: 20, angle: 45, g: 9.8, h0: 0, mass: 1 }
      }
    },
    {
      name: '测试 3：自由落体',
      data: {
        sub_type: 'free_fall',
        parameters: { height: 20, g: 9.8, mass: 1 }
      }
    }
  ];

  for (let i = 0; i < tests.length; i++) {
    const test = tests[i];
    console.log(`\n🧪 ${test.name}`);

    try {
      const engine = new AnimationEngine(canvas);
      engine.loadInstructions(test.data);
      engine.play();

      console.log('✅ 成功！');

      // 等待 2 秒观察动画
      await new Promise(resolve => setTimeout(resolve, 2000));
      engine.pause();

    } catch (error) {
      console.error('❌ 失败:', error);
    }
  }

  console.log('\n✨ 所有测试完成！');
})();
```

---

## 🐛 常见问题排查

### 问题 1：动画无法播放
**可能原因**：
- Canvas 元素不存在或 ID 错误
- 脚本加载顺序错误
- 数据格式不支持

**解决方法**：
```javascript
// 检查 Canvas
console.log(document.getElementById('animationCanvas'));

// 检查全局对象
console.log(window.AnimationEngine);
console.log(window.PhysicsVisualizer);
console.log(window.AnimationBase);
```

---

### 问题 2：控制台报错 "PhysicsVisualizer is not defined"
**原因**：animations/ 脚本未加载

**解决方法**：
检查 templates/index.html 中的脚本顺序：
```html
<!-- 必须在 animation.js 之前加载 -->
<script src="/animations/animation_base.js"></script>
<script src="/animations/free_fall.js"></script>
<script src="/animations/projectile_motion.js"></script>
<script src="/animations/physics_visualizer.js"></script>

<!-- 然后才是适配层 -->
<script src="/static/animation.js"></script>
```

---

### 问题 3：数据格式转换失败
**查看转换日志**：
```javascript
// 控制台应显示
[兼容层] 旧格式 → 新格式转换: {
  原始数据: {...},
  转换后: {...}
}
```

**手动测试转换**：
```javascript
const result = AnimationEngine.normalizePayload({
  type: 'projectile',
  initial_speed: 20,
  angle: 45
});

console.log(result);
// 应输出：{ sub_type: 'projectile_motion', parameters: {...} }
```

---

## 📊 测试报告模板

复制以下模板，填写验证结果：

```
## 动画模块验证报告

**测试时间**：2025-XX-XX
**测试环境**：Chrome/Safari/Firefox XX.X
**测试人员**：XXX

### 功能测试
- [ ] 旧格式抛体运动：通过/失败
- [ ] 新格式抛体运动：通过/失败
- [ ] 自由落体：通过/失败
- [ ] 播放控制：通过/失败
- [ ] 重播功能：通过/失败

### 兼容性测试
- [ ] 旧→新格式转换：通过/失败
- [ ] 控制台无报错：通过/失败

### 视觉测试
- [ ] 轨迹正确：通过/失败
- [ ] 速度向量正确：通过/失败
- [ ] 关键点标记：通过/失败

### 问题记录
（如有问题，请详细描述）

### 总体评价
通过 ✅ / 需修复 ⚠️
```

---

## 🚀 后续优化建议

1. **添加单元测试**：使用 Jest 或 Mocha 编写自动化测试
2. **性能监控**：记录帧率（FPS）和渲染时间
3. **错误边界**：添加更完善的错误处理和降级方案
4. **TypeScript 迁移**：提供类型定义文件（.d.ts）
5. **CI/CD 集成**：在提交前自动运行动画测试