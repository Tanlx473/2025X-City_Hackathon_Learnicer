# 2025X-City_Hackathon_Learnicer

A Flask-based backend with **Claude API 多模态一体化 Pipeline**（同时完成 OCR + 题目解析 + 动画指令生成），plus a lightweight front-end (HTML/CSS/JS) that renders solution steps and Canvas animations.

## Tech Stack
- Backend: Flask
- AI Pipeline: **Claude API** (多模态，一次性完成 OCR + 解析 + 动画指令)
- Frontend: HTML/CSS/JavaScript + Canvas

## 📋 Table of Contents
- [安全配置说明](#安全配置说明)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [OCR 配置](#ocr-配置)
- [测试接口](#测试接口)
- [支持的运动类型](#支持的运动类型)
- [故障排查](#故障排查)

---

## ⚠️ 安全配置说明

**本项目采用环境变量管理所有敏感配置（API Key、密钥等），确保安全性和团队协作友好性。**

### 快速开始配置

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑 .env 文件，填入 Claude API Key
vi .env  # 或 nano .env，或 code .env

# 3. 填入 Claude API Key
# CLAUDE_API_KEY=your_claude_api_key
```

### 重要规则

1. **绝不提交 `.env` 到 Git** - 已被 `.gitignore` 自动忽略
2. **只提交 `.env.example`** - 仅包含占位符，无真实密钥
3. **无需修改源代码** - 所有配置通过环境变量读取
4. **支持降级运行** - 未配置 API Key 时可使用 manual 模式

### 配置项说明

| 配置项 | 必需性 | 默认值 | 说明 |
|--------|--------|--------|------|
| `CLAUDE_API_KEY` | claude 模式必需 | 无 | Claude API 密钥 |
| `CLAUDE_MODEL` | 可选 | `claude-3-5-sonnet-20241022` | Claude 模型名称 |
| `PIPELINE_MODE` | 可选 | `claude` | Pipeline 模式（`claude`/`manual`） |

### 获取 API Key

#### Claude API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 创建 API Key
4. 复制到 `.env` 文件中的 `CLAUDE_API_KEY=`

### 无 API Key 也能运行（Manual 模式）

如果不配置 Claude API Key，可以使用 **manual 模式**：

```bash
export PIPELINE_MODE=manual
```

manual 模式特性：
- 支持通过 `manual_text` 参数直接传入题目文本
- 使用规则引擎解析题目（不调用 Claude API）
- 不同输入会产生不同的输出（避免硬编码）
- 适用于团队联调、CI、无 Key/离线测试场景

---

## Requirements

- Python: 3.8+
- pip: 20.2.2+
- 稳定的网络连接（Claude API 调用）

---

## Quick Start

### 1) 创建并激活虚拟环境

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) 安装依赖

```bash
pip install -r requirements.txt
```

### 3) 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入 Claude API Key
# CLAUDE_API_KEY=your_api_key
```

### 4) 启动后端

```bash
python app.py
```

或使用 Flask CLI：

```bash
flask --app app run --debug
```

### 5) 验证后端运行（健康检查）

```bash
curl http://127.0.0.1:5000/health
```

预期响应：
```json
{"status":"ok"}
```

### 6) 检查 Pipeline 状态

```bash
curl http://127.0.0.1:5000/pipeline/status
```

预期响应（claude 模式且已配置）：
```json
{
  "mode": "claude",
  "claude_configured": true,
  "error": null
}
```

---

## Pipeline 配置

### Pipeline 模式说明

本项目支持两种 Pipeline 模式，通过环境变量 `PIPELINE_MODE` 切换：

#### 1. Claude 模式（默认，推荐）

```bash
export PIPELINE_MODE=claude
export CLAUDE_API_KEY=your_api_key
```

**特点：**
- ✅ Claude 多模态一体化：OCR + 题目解析 + 动画指令生成一次完成
- ✅ 识别准确率高，支持数学公式、手写体、中英混合
- ✅ 智能提取物理参数和生成解题步骤
- ✅ 自动计算动画参数（duration, scale 等）
- ⚠️ 需要网络连接
- ⚠️ 需要 Claude API Key（访问 console.anthropic.com 获取）

#### 2. Manual 模式（测试/无 Key 场景）

```bash
export PIPELINE_MODE=manual
```

**特点：**
- ✅ 无需 API Key
- ✅ 支持通过 `manual_text` 参数直接传入题目文本
- ✅ 使用规则引擎解析（正则表达式提取参数）
- ✅ 不同输入会产生不同的输出（避免硬编码）
- ✅ 适用于团队联调、CI、无 Key/离线测试
- ⚠️ 不调用真实 OCR

**使用方式：**

```bash
# Manual 模式：直接提供题目文本
export PIPELINE_MODE=manual

curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²，求运动轨迹。"
```

---

## 测试接口

### 方式 1：Claude 模式 + 图片上传（完整流程）

```bash
# 确保已配置 CLAUDE_API_KEY
export PIPELINE_MODE=claude

curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test_image.jpg"
```

### 方式 2：Manual 模式 + 手动输入文本

```bash
export PIPELINE_MODE=manual

curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。"
```

### 测试样例

#### 样例 1：平抛运动

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。"
```

预期返回包含：
```json
{
  "problem_type": "physics_horizontal_projectile",
  "problem_text": "一个物体从8米高的平台以10m/s的速度水平抛出...",
  "solution_steps": ["...", "..."],
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 10,
    "angle": 0,
    "initial_y": 8,
    "gravity": 9.8,
    "duration": 1.28,
    "scale": 20
  }
}
```

#### 样例 2：自由落体

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从12米高处自由下落，g=10m/s²，求下落时间和落地速度。"
```

预期返回包含：
```json
{
  "problem_type": "physics_free_fall",
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 0,
    "angle": 90,
    "initial_y": 12,
    "gravity": 10
  }
}
```

---

## 支持的运动类型

| 运动类型 | 关键词 | 动画类型 | 参数要求 |
|---------|-------|---------|---------|
| 平抛运动 | "平抛"、"水平抛" | projectile (angle=0) | 初速度、高度 |
| 自由落体 | "自由落体"、"下落" | projectile (v0=0, angle=90) | 高度 |
| 竖直上抛 | "竖直上抛"、"上抛" | projectile (angle=90) | 初速度 |
| 斜抛运动 | "抛体"、"弹道" | projectile | 初速度、角度 |
| 匀速直线 | "匀速" | uniform | 速度 |

---

## 动画指令格式

前端 `animation.js` 期待的 `animation_instructions` 格式：

```json
{
  "type": "projectile",  // 或 "uniform"
  "initial_speed": 10.0,  // m/s
  "angle": 45,            // 度
  "gravity": 9.8,         // m/s²
  "initial_x": 0,         // 初始 x 坐标
  "initial_y": 0,         // 初始 y 坐标（高度）
  "duration": 2.5,        // 持续时间（秒）
  "scale": 20             // 可视化缩放比例
}
```

---

## 故障排查

### Claude Pipeline 调用失败

**问题：** `Claude API Key 未配置`

**解决方案：**
```bash
# 检查环境变量是否设置
echo $CLAUDE_API_KEY

# 重新配置
export CLAUDE_API_KEY=your_api_key

# 或编辑 .env 文件
vi .env
```

**问题：** `Claude API 返回错误（401/403）`

**解决方案：**
- 检查 API Key 是否有效（访问 console.anthropic.com）
- 确认 Claude 账户是否有剩余额度
- 确认使用的模型名称是否正确（默认：claude-3-5-sonnet-20241022）

**问题：** `Claude API 请求超时`

**解决方案：**
- 检查网络连接
- 尝试使用更小的图片（压缩后再上传）
- 临时切换到 manual 模式：`export PIPELINE_MODE=manual`

### OCR 识别不准确

**问题：** Claude 未能正确识别题目文字或公式

**解决方案：**
1. 确保图片清晰且包含文字/数学公式
2. 尝试提高图片分辨率或对比度
3. 查看后端日志获取详细错误信息
4. 使用 manual 模式手动输入题目文本：
   ```bash
   export PIPELINE_MODE=manual
   curl -X POST http://127.0.0.1:5000/upload \
     -F "manual_text=你的题目文本"
   ```

### 动画不显示

**问题：** 前端动画未播放

**解决方案：**
- 打开浏览器控制台查看错误信息
- 确认后端返回的 `animation_instructions` 字段包含所需参数
- 检查 `type` 字段是否为 "projectile"、"uniform"、"free_fall" 或 "inclined_plane"
- 验证参数值是否合理（例如 speed > 0, angle 在 0-360 之间）

### Manual 模式返回错误

**问题：** Manual 模式需要提供 manual_text 参数

**解决方案：**
```bash
# Manual 模式必须提供题目文本
export PIPELINE_MODE=manual

curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²"
```

---

## 前端使用

打开浏览器访问 `http://127.0.0.1:5000/`，即可：

1. 上传物理题图片（Claude 模式）或输入题目文本（Manual 模式）
2. 查看 AI 识别/解析的题目文字
3. 查看解题步骤
4. 观看 Canvas 动画演示物理运动
5. 使用播放/暂停/重播按钮控制动画

---

## Team Workflow

* 使用 `requirements.txt` 管理共享依赖
* **绝不提交** `.venv/` 或 `.env` 到 Git
* 如果添加依赖：
  * `pip install <pkg>`
  * 更新 `requirements.txt`（手动编辑推荐）

---

## Migration Notes

### 从 Mathpix OCR 迁移到 Claude 多模态 Pipeline（2025-12-28）

**主要变更：**
1. **OCR + 解析一体化**：移除 Mathpix OCR，改用 Claude API 多模态能力（同时完成 OCR + 题目解析 + 动画指令生成）
2. **简化依赖**：移除 Mathpix 相关依赖，保留 `anthropic`, `Flask`, `Pillow`
3. **环境变量调整**：
   - 移除：`MATHPIX_APP_ID`, `MATHPIX_APP_KEY`, `OCR_MODE`
   - 新增：`PIPELINE_MODE=claude|manual`
   - 保留：`CLAUDE_API_KEY`, `CLAUDE_MODEL`
4. **Manual 模式增强**：必须提供 `manual_text`，使用规则引擎解析（不再生成 hash 测试文本）
5. **新增 `/pipeline/status` 接口**，移除 `/ocr/status`

**兼容性：**
- `/upload` 接口保持不变
- 响应 JSON 格式保持不变（`problem_type`, `problem_text`, `solution_steps`, `animation_instructions`）
- `manual_text` 参数继续支持（且在 manual 模式下必需）

**迁移步骤：**
1. 更新 `.env`：移除 Mathpix 配置，添加 `PIPELINE_MODE=manual`（测试）或配置 `CLAUDE_API_KEY`（生产）
2. 测试 manual 模式：`export PIPELINE_MODE=manual && curl -X POST http://127.0.0.1:5000/upload -F "manual_text=..."`
3. 测试 claude 模式：`export PIPELINE_MODE=claude && curl -X POST http://127.0.0.1:5000/upload -F "file=@test.jpg"`

---

## License

Hackathon project.