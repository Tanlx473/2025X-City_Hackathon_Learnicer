# 2025X-City_Hackathon_Learnicer

A Flask-based backend with **Mathpix OCR** (cloud) for image-to-structured-output, plus a lightweight front-end (HTML/CSS/JS) that renders solution steps and Canvas animations.

## Tech Stack
- Backend: Flask
- OCR: **Mathpix API** (cloud-based, supports math/text/LaTeX)
- LLM: Anthropic Claude API (可选，支持降级)
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

# 2. 编辑 .env 文件，填入你的实际配置
vi .env  # 或 nano .env，或 code .env

# 3. 填入 Mathpix 和 Claude API Key
# MATHPIX_APP_ID=your_mathpix_app_id
# MATHPIX_APP_KEY=your_mathpix_app_key
# CLAUDE_API_KEY=your_claude_api_key  (可选)
```

### 重要规则

1. **绝不提交 `.env` 到 Git** - 已被 `.gitignore` 自动忽略
2. **只提交 `.env.example`** - 仅包含占位符，无真实密钥
3. **无需修改源代码** - 所有配置通过环境变量读取
4. **支持降级运行** - 未配置 API 时可使用 manual 模式

### 配置项说明

| 配置项 | 必需性 | 默认值 | 说明 |
|--------|--------|--------|------|
| `MATHPIX_APP_ID` | mathpix 模式必需 | 无 | Mathpix 应用 ID |
| `MATHPIX_APP_KEY` | mathpix 模式必需 | 无 | Mathpix 应用密钥 |
| `OCR_MODE` | 可选 | `mathpix` | OCR 模式（`mathpix`/`manual`） |
| `CLAUDE_API_KEY` | 可选 | 无 | Claude API 密钥（未配置则使用规则引擎） |

### 获取 API Keys

#### Mathpix API Key（OCR 必需）

1. 访问 [Mathpix Accounts](https://accounts.mathpix.com/)
2. 注册/登录账号
3. 创建应用并获取 `APP_ID` 和 `APP_KEY`
4. 复制到 `.env` 文件中

#### Claude API Key（可选）

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 创建 API Key
4. 复制到 `.env` 文件中的 `CLAUDE_API_KEY=`

### 无 API Key 也能运行（Manual 模式）

如果不配置 Mathpix API Key，可以使用 **manual 模式**：

```bash
export OCR_MODE=manual
```

manual 模式特性：
- 支持通过 `manual_text` 参数直接传入题目文本
- 若未提供 `manual_text`，会根据图片路径生成确定性的测试题目
- 不同输入会产生不同的输出（避免硬编码）
- 适用于 B/C 联调、CI、无 Key 场景

---

## Requirements

- Python: 3.8+
- pip: 20.2.2+
- 稳定的网络连接（Mathpix API 调用）

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

# 编辑 .env 文件，填入 Mathpix API Key
# MATHPIX_APP_ID=your_app_id
# MATHPIX_APP_KEY=your_app_key
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

### 6) 检查 OCR 状态

```bash
curl http://127.0.0.1:5000/ocr/status
```

预期响应（mathpix 模式且已配置）：
```json
{
  "mode": "mathpix",
  "mathpix_configured": true,
  "error": null
}
```

---

## OCR 配置

### OCR 模式说明

本项目支持两种 OCR 模式，通过环境变量 `OCR_MODE` 切换：

#### 1. Mathpix 模式（默认，推荐）

```bash
export OCR_MODE=mathpix
export MATHPIX_APP_ID=your_app_id
export MATHPIX_APP_KEY=your_app_key
```

**特点：**
- ✅ 云端 OCR，识别准确率高
- ✅ 支持数学公式、LaTeX、手写体
- ✅ 支持中英混合、多语言
- ✅ 返回结构化 HTML/Markdown
- ⚠️ 需要网络连接
- ⚠️ 需要 Mathpix API Key（免费额度：1000 次/月）

#### 2. Manual 模式（测试/无 Key 场景）

```bash
export OCR_MODE=manual
```

**特点：**
- ✅ 无需 API Key
- ✅ 支持通过 `manual_text` 参数直接输入文本
- ✅ 自动生成确定性测试题目（基于图片路径 hash）
- ✅ 适用于 B/C 联调、CI、离线测试
- ⚠️ 不调用真实 OCR

**使用方式：**

方式 A：提供 manual_text
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²"
```

方式 B：上传图片，自动生成测试题目
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test.jpg"
```

---

## 测试接口

### 方式 1：Mathpix 模式 + 图片上传（完整流程）

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test_image.jpg"
```

### 方式 2：Manual 模式 + 手动输入文本

```bash
export OCR_MODE=manual

curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。"
```

### 方式 3：Manual 模式 + 图片（自动生成测试题）

```bash
export OCR_MODE=manual

curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test.jpg"
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

### OCR 无法识别文本

**问题：** Mathpix API 返回空结果

**解决方案：**
1. 确保图片清晰且包含文字/数学公式
2. 检查 Mathpix API Key 是否正确配置
3. 检查网络连接
4. 查看后端日志获取详细错误信息
5. 使用 manual 模式跳过 OCR：
   ```bash
   export OCR_MODE=manual
   ```

### Mathpix API 调用失败

**问题：** `Mathpix API 凭证未配置`

**解决方案：**
```bash
# 检查环境变量是否设置
echo $MATHPIX_APP_ID
echo $MATHPIX_APP_KEY

# 重新配置
export MATHPIX_APP_ID=your_app_id
export MATHPIX_APP_KEY=your_app_key
```

**问题：** `Mathpix API 返回错误状态码: 401`

**解决方案：**
- 检查 API Key 是否有效
- 确认 Mathpix 账户是否有剩余额度
- 访问 [Mathpix Dashboard](https://accounts.mathpix.com/) 查看额度

**问题：** `Mathpix API 请求超时`

**解决方案：**
- 检查网络连接
- 尝试使用更小的图片
- 临时使用 manual 模式

### Claude API 调用失败

- 检查 `.env` 文件中的 `CLAUDE_API_KEY` 是否正确
- 查看后端日志，确认是否成功调用 API
- 如果 API 不可用，系统会自动降级使用规则引擎

### 动画不显示

- 打开浏览器控制台查看错误信息
- 确认后端返回的 `animation_instructions` 字段包含所需参数
- 检查 `type` 字段是否为 "projectile" 或 "uniform"

### Manual 模式返回固定文本

**问题：** 不同图片返回相同的测试题目

**解决方案：**
- Manual 模式会根据图片路径和修改时间生成 hash
- 确保上传了不同的图片文件
- 或使用 `manual_text` 参数手动指定不同的文本

---

## 前端使用

打开浏览器访问 `http://127.0.0.1:5000/`，即可：

1. 上传物理题图片
2. 查看 OCR 识别结果
3. 查看解题步骤
4. 观看 Canvas 动画演示
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

### 从 PaddleOCR 迁移到 Mathpix

**主要变更：**
1. OCR 引擎从 PaddleOCR（本地）切换到 Mathpix（云端）
2. 移除 `paddleocr`, `paddlepaddle`, `opencv-python` 依赖
3. 环境变量 `OCR_PROVIDER` 改名为 `OCR_MODE`
4. Manual 模式增强：自动生成确定性测试文本（避免硬编码）

**兼容性：**
- `/upload` 接口保持不变
- 响应 JSON 格式保持不变
- `manual_text` 参数继续支持

---

## License

Hackathon project.