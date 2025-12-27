# 前端测试指南

## 🚀 快速开始

### 1. 确认后端运行中
```bash
curl http://127.0.0.1:5000/health
# 应该返回: {"status":"ok"}
```

### 2. 打开浏览器
```
http://127.0.0.1:5000/
```

---

## 📋 测试清单

### ✅ 测试 1：界面加载
- [ ] 页面标题显示："物理题目可视化解题工具"
- [ ] 上传表单可见
- [ ] Canvas 画布可见（720x420px）
- [ ] 控制按钮隐藏（初始状态）

### ✅ 测试 2：使用浏览器控制台直接测试动画（无需上传图片）

打开浏览器控制台（F12 或 右键 → 检查 → Console），粘贴以下代码：

#### 测试 2.1：平抛运动
```javascript
// 平抛运动测试数据
const horizontalProjectileData = {
  type: 'projectile',
  initial_speed: 10,
  angle: 0,
  gravity: 9.8,
  initial_x: 0,
  initial_y: 8,
  duration: 1.28,
  scale: 30
};

const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);
engine.loadInstructions(horizontalProjectileData);
engine.play();

// 显示控制按钮
document.getElementById('controls').style.display = 'flex';
document.getElementById('playBtn').onclick = () => engine.play();
document.getElementById('pauseBtn').onclick = () => engine.pause();
document.getElementById('replayBtn').onclick = () => { engine.reset(); engine.play(); };

console.log('✅ 平抛运动动画已加载，持续时间:', horizontalProjectileData.duration, '秒');
```

**预期效果：**
- 红色小球从画布左侧上方（8m高）开始
- 水平向右飞出，同时向下加速
- 形成抛物线轨迹
- 蓝色箭头表示速度方向
- 橙色线显示运动轨迹

#### 测试 2.2：自由落体
```javascript
// 自由落体测试数据
const freeFallData = {
  type: 'projectile',
  initial_speed: 0,
  angle: 90,
  gravity: 10,
  initial_x: 0,
  initial_y: 12,
  duration: 1.55,
  scale: 30
};

const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);
engine.loadInstructions(freeFallData);
engine.play();

console.log('✅ 自由落体动画已加载，持续时间:', freeFallData.duration, '秒');
```

**预期效果：**
- 红色小球从高处（12m）静止开始
- 垂直向下加速运动
- 速度箭头逐渐变长
- 约 1.55 秒后落地

#### 测试 2.3：斜抛运动
```javascript
// 斜抛运动测试数据
const projectileData = {
  type: 'projectile',
  initial_speed: 15,
  angle: 45,
  gravity: 9.8,
  initial_x: 0,
  initial_y: 0,
  duration: 2.16,
  scale: 20
};

const canvas = document.getElementById('animationCanvas');
const engine = new AnimationEngine(canvas);
engine.loadInstructions(projectileData);
engine.play();

console.log('✅ 斜抛运动动画已加载');
```

**预期效果：**
- 红色小球从左下角开始
- 以 45° 角向右上方飞出
- 形成完整的抛物线
- 先上升后下落

### ✅ 测试 3：模拟完整上传流程（使用 fetch）

在浏览器控制台执行：

```javascript
// 模拟上传请求（使用 manual_text）
async function testUpload(questionText) {
  console.log('📤 发送请求...');

  const formData = new FormData();
  formData.append('manual_text', questionText);

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    console.log('✅ 后端响应:', data);

    // 渲染解题步骤
    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '<ol>' +
      data.solution_steps.map(s => `<li>${s}</li>`).join('') +
      '</ol>';

    // 渲染动画指令
    const instructionsContainer = document.getElementById('instructionsContainer');
    instructionsContainer.innerHTML = `<pre>${JSON.stringify(data.animation_instructions, null, 2)}</pre>`;

    // 渲染题目信息
    const metaContainer = document.getElementById('metaContainer');
    metaContainer.innerHTML = `
      <ul>
        <li><strong>题目类型：</strong>${data.problem_type}</li>
        <li><strong>运动类型：</strong>${data.parameters.motion_type}</li>
      </ul>
    `;

    // 加载并播放动画
    const canvas = document.getElementById('animationCanvas');
    const engine = new AnimationEngine(canvas);
    engine.loadInstructions(data.animation_instructions);
    engine.play();

    // 显示控制按钮
    const controls = document.getElementById('controls');
    controls.style.display = 'flex';
    document.getElementById('playBtn').onclick = () => engine.play();
    document.getElementById('pauseBtn').onclick = () => engine.pause();
    document.getElementById('replayBtn').onclick = () => { engine.reset(); engine.play(); };

    console.log('✅ 动画已加载并开始播放');
    return data;
  } catch (error) {
    console.error('❌ 错误:', error);
    throw error;
  }
}

// 测试平抛运动
testUpload('一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。');
```

**预期效果：**
- 控制台显示请求日志
- 页面左侧显示解题步骤
- 页面左侧显示动画指令 JSON
- Canvas 播放平抛运动动画
- 控制按钮出现并可用

### ✅ 测试 4：控制按钮功能

**测试步骤：**
1. 动画播放中，点击"暂停"按钮
   - ✅ 动画应该暂停，小球静止

2. 点击"播放"按钮
   - ✅ 动画应该继续播放

3. 等待动画播放完毕，点击"重播"按钮
   - ✅ 动画应该从头开始重新播放

### ✅ 测试 5：错误处理

在控制台测试错误情况：

```javascript
// 测试空文本
testUpload('').catch(err => console.log('✅ 正确处理了空文本错误'));

// 测试无效文本
testUpload('这是一段无关的文字').then(data => {
  console.log('✅ 降级处理成功，返回了默认动画');
});
```

---

## 🎨 视觉检查清单

### Canvas 动画
- [ ] 背景网格清晰可见
- [ ] y=0 地面线显示
- [ ] 红色小球（半径 8px）可见
- [ ] 蓝色速度箭头随运动变化
- [ ] 橙色运动轨迹逐渐绘制
- [ ] 动画流畅，无卡顿

### 界面布局
- [ ] 左侧文本区域和右侧动画区域分栏显示
- [ ] 响应式布局（缩放浏览器窗口测试）
- [ ] 字体清晰易读
- [ ] 按钮样式美观

---

## 🐛 常见问题排查

### 问题 1：Canvas 空白
**解决方法：**
```javascript
// 在控制台检查
const canvas = document.getElementById('animationCanvas');
console.log('Canvas:', canvas);
console.log('Width:', canvas.width, 'Height:', canvas.height);
```

### 问题 2：动画不播放
**解决方法：**
```javascript
// 检查动画引擎状态
console.log('Engine:', engine);
console.log('Is playing:', engine.isPlaying);
console.log('Duration:', engine.duration);
```

### 问题 3：后端请求失败
**解决方法：**
```bash
# 在终端检查后端日志
tail -50 backend.log
```

---

## 📱 移动端测试（可选）

### 使用手机访问
1. 确保手机和电脑在同一局域网
2. 查看电脑 IP：
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
3. 手机浏览器访问：`http://<电脑IP>:5000/`

**移动端检查：**
- [ ] 页面正常显示
- [ ] Canvas 自适应屏幕
- [ ] 触摸操作正常
- [ ] 动画流畅

---

## ✅ 完整功能演示脚本

在控制台运行完整演示：

```javascript
async function fullDemo() {
  console.log('🎬 开始完整演示...\n');

  const samples = [
    {
      name: '平抛运动',
      text: '一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。'
    },
    {
      name: '自由落体',
      text: '一个物体从12米高处自由下落，g=10m/s²，求下落时间和落地速度。'
    },
    {
      name: '斜抛运动',
      text: '将一个物体以15m/s的初速度、与水平面成45度角斜向上抛出，g=9.8m/s²，求物体的射程和最大高度。'
    }
  ];

  for (let i = 0; i < samples.length; i++) {
    const sample = samples[i];
    console.log(`\n${i + 1}. 测试 ${sample.name}...`);

    try {
      await testUpload(sample.text);
      console.log(`✅ ${sample.name} 测试成功\n`);

      // 等待动画播放 3 秒
      if (i < samples.length - 1) {
        console.log('⏳ 等待 3 秒后继续...');
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    } catch (error) {
      console.error(`❌ ${sample.name} 测试失败:`, error);
    }
  }

  console.log('\n🎉 演示完成！');
}

// 运行完整演示
fullDemo();
```

---

## 📊 测试报告模板

完成测试后，填写此报告：

```
## 前端测试报告

测试时间: __________
测试浏览器: __________
后端状态: ✅ / ❌

### 功能测试
- [ ] 界面加载正常
- [ ] 控制台动画测试通过
- [ ] 模拟上传测试通过
- [ ] 控制按钮功能正常
- [ ] 错误处理正确

### 动画测试
- [ ] 平抛运动动画正常
- [ ] 自由落体动画正常
- [ ] 斜抛运动动画正常
- [ ] 轨迹绘制正确
- [ ] 速度向量显示正确

### 问题记录
1. __________
2. __________

### 总体评价
__________
```

---

## 🎯 下一步

完成前端测试后，可以：
1. 尝试上传真实的物理题图片
2. 调整 Canvas 样式和动画参数
3. 添加更多运动类型支持
4. 优化移动端体验