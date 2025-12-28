# 动画模块兼容性验证指南

## 概述

本文档提供端到端测试步骤，验证 `animations/` 新动画模块与前后端代码的兼容性。

---

## 快速测试（必做）

### 1. 启动服务

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 启动 Flask 服务
python app.py
```

服务应在 http://127.0.0.1:5000 启动。

### 2. 打开浏览器控制台

打开 http://127.0.0.1:5000，按 F12 打开开发者工具的 Console 标签。

### 3. 测试场景 A：抛体运动（Projectile Motion）

**模拟输入：**

在浏览器控制台执行以下代码（模拟后端返回）：

```javascript
// 模拟后端返回的抛体运动数据
const testData = {
  type: 'projectile',
  initial_speed: 20,
  angle: 45,
  gravity: 9.8,
  initial_x: 0,
  initial_y: 0,
  duration: 4
};

// 获取画布和引擎
const canvas = document.getElementById('animationCanvas');
const testEngine = new AnimationEngine(canvas);

// 加载并播放
testEngine.loadInstructions(testData);
testEngine.play();
```

**预期结果：**
- ✅ 控制台显示：`[兼容层] 旧格式 → 新格式转换`
- ✅ Canvas 显示抛体运动轨迹（红色小球，带轨迹线）
- ✅ 小球完整运动并落地
- ✅ 无报错

---

### 4. 测试场景 B：自由落体（Free Fall）

```javascript
const testData = {
  type: 'free_fall',
  initial_y: 15,
  gravity: 9.8
};

const canvas = document.getElementById('animationCanvas');
const testEngine = new AnimationEngine(canvas);
testEngine.loadInstructions(testData);
testEngine.play();
```

**预期结果：**
- ✅ Canvas 显示自由落体（小球从高处垂直下落）
- ✅ 无 `params.height is undefined` 报错（已修复参数兼容性）

---

### 5. 测试场景 C：匀速运动（Uniform Motion）

```javascript
const testData = {
  type: 'uniform',
  initial_speed: 10,
  angle: 30,
  duration: 8
};

const canvas = document.getElementById('animationCanvas');
const testEngine = new AnimationEngine(canvas);
testEngine.loadInstructions(testData);
testEngine.play();
```

**预期结果：**
- ✅ Canvas 显示匀速直线运动（绿色小球，恒定速度）
- ✅ 无 `vx is undefined` 报错（已修复参数转换）

---

### 6. 测试控制按钮

在运行任一动画后，测试页面控制按钮：

- **播放按钮**：动画继续
- **暂停按钮**：动画暂停
- **重播按钮**：动画从头开始

**预期结果：**
- ✅ 所有按钮正常响应
- ✅ 无重复初始化报错

---

## 完整测试（推荐）

### 7. 测试真实图片上传（需要配置 Claude API）

**前提：** 设置环境变量 `CLAUDE_API_KEY`

```bash
export CLAUDE_API_KEY=your_api_key
export PIPELINE_MODE=claude
```

**步骤：**

1. 准备一张物理题目图片（抛体运动、自由落体等）
2. 在页面上传图片
3. 等待后端处理（可能需要 10-30 秒）
4. 观察返回结果

**预期结果：**
- ✅ 显示解题步骤
- ✅ 显示动画指令（JSON）
- ✅ 动画自动播放
- ✅ 动画类型与题目一致（projectile/free_fall/uniform）

---

### 8. 测试 Manual 模式（无需 API）

```bash
export PIPELINE_MODE=manual
```

使用 `curl` 提交文本：

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F 'manual_text=一个物体以 20m/s 的初速度，与水平方向成 45° 角抛出，求最大高度和水平射程。g=9.8m/s²'
```

**预期结果：**
- ✅ 返回 JSON，包含 `animation_instructions.type = "projectile"`
- ✅ 前端接收后正确显示动画

---

## 错误排查

### 常见问题 1：`updatePhysicsPanel is not defined`

**原因：** HTML 缺少全局函数定义
**解决：** 已在 `templates/index.html` 添加占位函数（第 87-94 行）
**验证：** 检查控制台是否还有此报错

---

### 常见问题 2：`Uniform is not defined` 或 `UniformAcceleration is not defined`

**原因：** HTML 缺少脚本引用
**解决：** 已在 `templates/index.html` 添加：

```html
<script src="/animations/uniform.js"></script>
<script src="/animations/uniform_acceleration.js"></script>
<script src="/animations/uniform_circular.js"></script>
```

**验证：** 检查网络标签（Network）是否成功加载这些文件（状态码 200）

---

### 常见问题 3：动画不显示，但无报错

**可能原因：**
- Canvas 尺寸太小
- 动画参数导致物体飞出画布

**排查：**

```javascript
// 检查动画对象是否存在
console.log(testEngine.visualizer.currentAnimation);

// 检查 Canvas 尺寸
console.log(canvas.width, canvas.height);

// 检查物理参数
console.log(testEngine.visualizer.currentAnimation.objects[0]);
```

---

## 验证清单

完成以下所有项即表示兼容性测试通过：

- [ ] 场景 A：抛体运动正常显示
- [ ] 场景 B：自由落体正常显示
- [ ] 场景 C：匀速运动正常显示
- [ ] 控制按钮（播放/暂停/重播）正常工作
- [ ] 控制台无报错（updatePhysicsPanel, params.height, vx, Uniform 等）
- [ ] 多次上传/切换动画无内存泄漏或重复初始化
- [ ] （可选）真实图片上传测试通过

---

## 数据契约参考

### 后端返回格式

```json
{
  "problem_type": "projectile",
  "problem_text": "...",
  "solution_steps": ["步骤1", "步骤2", ...],
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 20,
    "angle": 45,
    "gravity": 9.8,
    "initial_x": 0,
    "initial_y": 0,
    "duration": 4,
    "scale": 20
  },
  "parameters": { ... }
}
```

### 适配器转换后格式

```json
{
  "sub_type": "projectile_motion",
  "parameters": {
    "v0": 20,
    "angle": 45,
    "g": 9.8,
    "h0": 0,
    "mass": 1
  }
}
```

---

## 支持的动画类型

| 后端 `type`         | 适配器 `sub_type`      | 动画类                |
|---------------------|------------------------|-----------------------|
| projectile          | projectile_motion      | ProjectileMotion      |
| free_fall           | free_fall              | FreeFall              |
| uniform             | uniform                | Uniform               |
| uniform_acceleration| uniform_acceleration   | UniformAcceleration   |
| uniform_circular    | uniform_circular       | UniformCircular       |
| inclined_plane      | incline_plane          | (待实现)              |

---

## 下一步

如果测试全部通过，可以：

1. 部署到生产环境
2. 添加更多动画类型（inclined_plane, circular_motion 等）
3. 优化动画参数的自动计算（scale, duration）
4. 实现物理参数实时面板（替换当前的 `updatePhysicsPanel` 占位函数）

---

**文档版本：** v1.0
**最后更新：** 2025-12-28
**维护者：** Claude Code