# 如何验证修复效果

本文档说明如何验证上传不同图片后，前端能够正确显示不同的动画效果。

## 快速验证（推荐）

### 方法 1: 使用浏览器手动测试

1. **启动应用**：
   ```bash
   python app.py
   ```

2. **打开浏览器**：
   访问 http://127.0.0.1:5000/

3. **打开开发者工具**：
   按 F12 或右键 → 检查

4. **使用 manual_text 参数测试**（绕过 OCR）：

   在浏览器控制台（Console）中运行：

   ```javascript
   // 测试 1: 平抛运动
   async function test1() {
     const formData = new FormData();
     formData.append('manual_text', '一小球以 15 m/s 的初速度水平抛出，从 10 米高的平台');

     const response = await fetch('/upload', {
       method: 'POST',
       body: formData
     });

     const data = await response.json();
     console.log('平抛运动:', {
       angle: data.animation_instructions.angle,
       speed: data.animation_instructions.initial_speed,
       height: data.animation_instructions.initial_y,
       motion_type: data.animation_instructions.motion_type_original
     });

     // 显示动画
     engine = new AnimationEngine(document.getElementById('animationCanvas'));
     engine.loadInstructions(data.animation_instructions);
     engine.play();
   }

   // 测试 2: 自由落体
   async function test2() {
     const formData = new FormData();
     formData.append('manual_text', '一物体从 20 米高处自由落体');

     const response = await fetch('/upload', {
       method: 'POST',
       body: formData
     });

     const data = await response.json();
     console.log('自由落体:', {
       angle: data.animation_instructions.angle,
       speed: data.animation_instructions.initial_speed,
       height: data.animation_instructions.initial_y,
       motion_type: data.animation_instructions.motion_type_original
     });

     engine = new AnimationEngine(document.getElementById('animationCanvas'));
     engine.loadInstructions(data.animation_instructions);
     engine.play();
   }

   // 测试 3: 斜抛运动
   async function test3() {
     const formData = new FormData();
     formData.append('manual_text', '以 25 m/s 的初速度以 60° 角斜向上抛出');

     const response = await fetch('/upload', {
       method: 'POST',
       body: formData
     });

     const data = await response.json();
     console.log('斜抛运动:', {
       angle: data.animation_instructions.angle,
       speed: data.animation_instructions.initial_speed,
       height: data.animation_instructions.initial_y,
       motion_type: data.animation_instructions.motion_type_original
     });

     engine = new AnimationEngine(document.getElementById('animationCanvas'));
     engine.loadInstructions(data.animation_instructions);
     engine.play();
   }

   // 运行测试
   await test1();  // 观察：水平抛出（angle=0）
   await test2();  // 观察：垂直下落（angle=90, speed=0）
   await test3();  // 观察：60度斜抛
   ```

5. **验证结果**：

   控制台应显示：
   ```
   平抛运动: {angle: 0, speed: 15, height: 10, motion_type: "horizontal_projectile"}
   自由落体: {angle: 90, speed: 0, height: 20, motion_type: "free_fall"}
   斜抛运动: {angle: 60, speed: 25, height: 0, motion_type: "projectile"}
   ```

   Canvas 应显示三种**明显不同**的运动轨迹。

### 方法 2: 使用命令行测试（推荐）

```bash
# 启动应用
python app.py &

# 测试平抛运动
curl -X POST http://127.0.0.1:5000/upload \
  -F 'manual_text=一小球以 15 m/s 的初速度水平抛出，从 10 米高的平台' \
  -s | python3 -c "
import json, sys
data = json.load(sys.stdin)
anim = data['animation_instructions']
print(f\"平抛: angle={anim['angle']}, speed={anim['initial_speed']}, height={anim['initial_y']}\")
print(f\"预期: angle=0, speed=15, height=10\")
print(f\"✅ 通过\" if anim['angle'] == 0 and anim['initial_speed'] == 15 else \"❌ 失败\")
"

# 测试自由落体
curl -X POST http://127.0.0.1:5000/upload \
  -F 'manual_text=一物体从 20 米高处自由落体' \
  -s | python3 -c "
import json, sys
data = json.load(sys.stdin)
anim = data['animation_instructions']
print(f\"自由落体: angle={anim['angle']}, speed={anim['initial_speed']}, height={anim['initial_y']}\")
print(f\"预期: angle=90, speed=0, height=20\")
print(f\"✅ 通过\" if anim['angle'] == 90 and anim['initial_speed'] == 0 else \"❌ 失败\")
"

# 测试斜抛运动
curl -X POST http://127.0.0.1:5000/upload \
  -F 'manual_text=以 25 m/s 的初速度以 60° 角斜向上抛出' \
  -s | python3 -c "
import json, sys
data = json.load(sys.stdin)
anim = data['animation_instructions']
print(f\"斜抛: angle={anim['angle']}, speed={anim['initial_speed']}, height={anim['initial_y']}\")
print(f\"预期: angle=60, speed=25, height=0\")
print(f\"✅ 通过\" if anim['angle'] == 60 and anim['initial_speed'] == 25 else \"❌ 失败\")
"
```

预期输出：
```
平抛: angle=0, speed=15, height=10
预期: angle=0, speed=15, height=10
✅ 通过

自由落体: angle=90, speed=0, height=20
预期: angle=90, speed=0, height=20
✅ 通过

斜抛: angle=60, speed=25, height=0
预期: angle=60, speed=25, height=0
✅ 通过
```

## 自动化测试

### 运行完整测试套件

```bash
# 后端单元测试（规则引擎）
python scripts/test_dynamic_response.py

# 端到端测试（需要先启动服务）
python app.py &
sleep 3
python scripts/test_upload_endpoint.py

# 前端集成测试
python scripts/test_frontend_integration.py
```

所有测试应该都通过（返回退出码 0）。

## 使用真实图片测试

如果你有物理题图片，可以直接上传：

1. 访问 http://127.0.0.1:5000/
2. 点击"选择图片文件"
3. 上传不同的物理题图片
4. 观察：
   - 解题步骤应该不同
   - 动画参数应该不同
   - Canvas 动画应该明显不同

## 验证检查清单

- [ ] 后端返回的 `animation_instructions` 确实不同
- [ ] 前端 `normalizePayload` 正确保留了 `angle=0` 等 falsy 值
- [ ] Canvas 动画显示不同的轨迹（不都是45度抛物线）
- [ ] 平抛运动显示为**水平抛出**（不是斜向上）
- [ ] 自由落体显示为**垂直下落**（无初速度）
- [ ] 斜抛运动正确显示为指定角度

## 常见问题排查

### Q: 动画还是都一样？

A: 检查浏览器控制台：
```javascript
// 在 main.js:120 行添加日志（临时）
console.log('[兼容层] 旧格式 → 新格式转换:', {
  原始数据: data,
  转换后: normalized
});
```

验证 `normalized.parameters.angle` 是否正确（应该是 0, 60, 90 等，而不是都是 45）。

### Q: 后端返回的数据一样？

A: 检查 `.env` 文件：
- 确保 `CLAUDE_API_KEY` 已配置（或留空使用规则引擎）
- 确保 `OCR_PROVIDER=paddle`（或使用 `manual_text` 参数）

### Q: OCR 识别不准？

A: 使用 `manual_text` 参数绕过 OCR：
```bash
curl -F 'manual_text=你的题目文本' http://127.0.0.1:5000/upload
```

或在浏览器开发者工具中：
```javascript
const formData = new FormData();
formData.append('manual_text', '你的题目文本');
fetch('/upload', {method: 'POST', body: formData});
```

## 预期修复效果对比

### 修复前 ❌
- 平抛运动：显示为 45 度斜抛
- 自由落体：有初速度 20 m/s
- 斜抛运动：参数可能正确，但其他都错
- **所有动画看起来都差不多**

### 修复后 ✅
- 平抛运动：正确显示为水平抛出（0 度）
- 自由落体：正确显示为无初速度垂直下落（90 度，v0=0）
- 斜抛运动：正确显示为指定角度（如 60 度）
- **不同题目显示明显不同的运动轨迹**

## 技术细节

修复的核心是 `static/animation.js` 的这个改动：

```diff
- angle: raw.angle || 45,
+ angle: raw.angle !== undefined ? raw.angle : 45,
```

这确保了 `angle=0`（平抛运动）不会被错误地替换为 `45`。

## 结论

如果所有测试通过，说明：
1. ✅ 后端正确从不同图片提取不同参数
2. ✅ 前端正确传递所有参数（包括 0 值）
3. ✅ 动画引擎正确显示不同的运动轨迹

**上传不同图片现在能够产生不同的动画效果！**