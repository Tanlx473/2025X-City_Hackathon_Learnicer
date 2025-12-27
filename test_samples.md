# 测试样例集

本文档提供可直接使用的测试样例，帮助快速验证系统功能。

## 快速测试命令

确保后端已启动（`python app.py`），然后在另一个终端执行以下命令。

---

## 样例 1：平抛运动（Horizontal Projectile）

### 题目文本
```
一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。
```

### 测试命令
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。"
```

### 预期输出关键字段
```json
{
  "problem_type": "physics_horizontal_projectile",
  "parameters": {
    "motion_type": "horizontal_projectile",
    "initial_speed": 10,
    "initial_height": 8,
    "gravity": 9.8
  },
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 10,
    "angle": 0,
    "gravity": 9.8,
    "initial_x": 0,
    "initial_y": 8,
    "duration": "约1.28秒",
    "scale": "自动计算"
  }
}
```

---

## 样例 2：自由落体（Free Fall）

### 题目文本
```
一个物体从12米高处自由下落，g=10m/s²，求下落时间和落地速度。
```

### 测试命令
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从12米高处自由下落，g=10m/s²，求下落时间和落地速度。"
```

### 预期输出关键字段
```json
{
  "problem_type": "physics_free_fall",
  "parameters": {
    "motion_type": "free_fall",
    "initial_speed": 0,
    "initial_height": 12,
    "gravity": 10
  },
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 0,
    "angle": 90,
    "gravity": 10,
    "initial_x": 0,
    "initial_y": 12,
    "duration": "约1.55秒"
  }
}
```

---

## 样例 3：竖直上抛（Vertical Throw）

### 题目文本
```
以20m/s的初速度竖直向上抛出一个小球，g取10m/s²，求小球上升的最大高度和落回地面的时间。
```

### 测试命令
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=以20m/s的初速度竖直向上抛出一个小球，g取10m/s²，求小球上升的最大高度和落回地面的时间。"
```

### 预期输出关键字段
```json
{
  "problem_type": "physics_vertical_throw",
  "parameters": {
    "motion_type": "vertical_throw",
    "initial_speed": 20,
    "angle": 90,
    "gravity": 10
  },
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 20,
    "angle": 90,
    "gravity": 10,
    "duration": "约4秒"
  }
}
```

---

## 样例 4：斜抛运动（General Projectile）

### 题目文本
```
将一个物体以15m/s的初速度、与水平面成45度角斜向上抛出，g=9.8m/s²，求物体的射程和最大高度。
```

### 测试命令
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=将一个物体以15m/s的初速度、与水平面成45度角斜向上抛出，g=9.8m/s²，求物体的射程和最大高度。"
```

### 预期输出关键字段
```json
{
  "problem_type": "physics_projectile",
  "parameters": {
    "motion_type": "projectile",
    "initial_speed": 15,
    "angle": 45,
    "gravity": 9.8
  },
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 15,
    "angle": 45,
    "gravity": 9.8
  }
}
```

---

## 样例 5：匀速直线运动（Uniform Motion）

### 题目文本
```
一辆汽车以5m/s的速度匀速行驶，求10秒后的位移。
```

### 测试命令
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一辆汽车以5m/s的速度匀速行驶，求10秒后的位移。"
```

### 预期输出关键字段
```json
{
  "problem_type": "physics_uniform",
  "parameters": {
    "motion_type": "uniform",
    "initial_speed": 5
  },
  "animation_instructions": {
    "type": "uniform",
    "initial_speed": 5,
    "angle": 0
  }
}
```

---

## 验证动画播放

完成上述测试后，可以在前端验证：

1. 打开浏览器访问 `http://127.0.0.1:5000/`
2. 点击"选择文件"按钮
3. 或者，在浏览器控制台执行以下代码直接加载动画：

```javascript
// 平抛运动示例
const animationData = {
  type: 'projectile',
  initial_speed: 10,
  angle: 0,
  gravity: 9.8,
  initial_x: 0,
  initial_y: 8,
  duration: 1.28,
  scale: 24
};

const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);
engine.loadInstructions(animationData);
engine.play();
```

---

## 故障排查

### 如果返回 400/500 错误

1. 检查后端日志，查看具体错误信息
2. 确认 `manual_text` 参数拼写正确
3. 如果使用图片上传，确认文件格式为 jpg/png/jpeg

### 如果 Claude API 未响应

1. 检查 `.env` 文件是否正确配置 `CLAUDE_API_KEY`
2. 查看后端日志中是否有"调用 Claude API"的信息
3. 如果未配置 API key，系统会自动降级使用规则引擎

### 如果动画不显示

1. 打开浏览器控制台，查看是否有 JavaScript 错误
2. 确认返回的 JSON 中包含 `animation_instructions` 字段
3. 检查 `animation_instructions.type` 是否为 "projectile" 或 "uniform"
4. 尝试手动在控制台加载动画（见上方示例）

---

## 生成新样例

可以根据以下模板创建新的测试样例：

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=<你的物理题文本>"
```

确保题目包含：
- 运动类型关键词（平抛、自由落体、上抛等）
- 数值参数（速度、高度、角度等）
- 单位（m/s、m、度等）

LLM 会自动识别并提取这些信息。