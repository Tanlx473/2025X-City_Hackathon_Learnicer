# 2025X-City_Hackathon_Learnicer

A Flask-based backend with PaddleOCR for image-to-structured-output, plus a lightweight front-end (HTML/CSS/JS) that renders solution steps and Canvas animations.

## Tech Stack
- Backend: Flask
- OCR: PaddleOCR (PaddlePaddle)
- Frontend: HTML/CSS/JavaScript + Canvas

## Requirements
- Python: 3.13
- pip: 20.2.2+
- macOS: PaddlePaddle on macOS is CPU-only and requires ARM64 (Mac M series). (No longer supports x86_64)  
  See official install guide.  

## Project Setup

### 1) Create & activate a virtual environment
创建并激活虚拟环境

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
````

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) Install PaddlePaddle 
安装 PaddlePaddle
由于不同系统/架构安装方式不同，paddlepaddle 故意没有写进 requirements.txt，请先单独安装。

Official command (CPU-only on macOS):

```bash
python3 -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

Verify:

```bash
python -c "import paddle; paddle.utils.run_check()"
```

Notes:

* Ensure your Python is ARM64 on Mac M series:

```bash
python -c "import platform; print(platform.architecture()[0]); print(platform.machine())"
# Expect: 64bit + arm64
```

### 3) Install remaining Python dependencies
安装其余依赖

```bash
pip install -r requirements.txt
```

### 4) Run backend 
启动后端

```bash
python app.py
```

### 5) Verify backend is working (health check)
验证后端运行（健康检查）
```bash
curl http://127.0.0.1:5000/health
```
Expected response:
```bash
{"status":"ok"}
```

### 6) Test image upload API
测试上传接口
使用本地图片文件（将 `test.jpg` 替换为你的路径）：

```bash
curl -X POST http://127.0.0.1:5000/upload -F "file=@test.jpg"
```
Expected: a JSON response that includes at least:

- `ocr_text`

- `solution_steps`

- `animation_instructions`


## Known Issue (Python 3.13 + PaddleOCR Import Error)

On Python 3.13, `import paddleocr` may fail due to a transitive dependency (`modelscope`) expecting `HUB_DATASET_ENDPOINT` to be set.

Workaround: set the env var before importing PaddleOCR:

Option A — set in code (recommended in backend entrypoint):
推荐方案：在导入 PaddleOCR 之前（例如 `app.py` 最顶部或注册路由之前）在代码中设置：

```python
import os
os.environ.setdefault("HUB_DATASET_ENDPOINT", "https://modelscope.cn/api/v1/datasets")
```

Option B — set in shell:
备选方案：在终端中设置：

```bash
export HUB_DATASET_ENDPOINT="https://modelscope.cn/api/v1/datasets"
```

## Run (example)

If your Flask entry is `app.py` at repo root:

```bash
python app.py
```

Or using Flask CLI:

```bash
flask --app app run --debug
```

Then open:

* [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

运行方式（示例）
如果入口为根目录 `app.py`：
```bash
python app.py
```

或使用 Flask CLI：
```bash
flask --app app run --debug
```
打开：
```
http://127.0.0.1:5000/
```


## 7) 配置 Claude API（必需，用于智能解析）

本项目使用 Claude API 进行物理题的智能解析和动画指令生成。

### 获取 Claude API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建账号并获取 API Key

### 配置环境变量

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑 .env 文件，填入你的 Claude API Key
# CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 降级方案（无需 API Key）

如果未配置 `CLAUDE_API_KEY`，系统将自动使用规则引擎降级方案：
- 通过正则表达式提取参数
- 准确率较低，但可以跑通演示

## 8) 测试接口

### 方式 1：图片上传（完整流程）

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test_image.jpg"
```

### 方式 2：手动输入文本（跳过 OCR，用于调试）

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "manual_text=一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²，求运动轨迹"
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
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 10,
    "angle": 0,
    "initial_y": 8,
    "gravity": 9.8,
    "duration": ...,
    "scale": ...
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

## 9) 前端使用

打开浏览器访问 `http://127.0.0.1:5000/`，即可：

1. 上传物理题图片
2. 查看 OCR 识别结果
3. 查看解题步骤
4. 观看 Canvas 动画演示
5. 使用播放/暂停/重播按钮控制动画

## 支持的运动类型

| 运动类型 | 关键词 | 动画类型 | 参数要求 |
|---------|-------|---------|---------|
| 平抛运动 | "平抛"、"水平抛" | projectile (angle=0) | 初速度、高度 |
| 自由落体 | "自由落体"、"下落" | projectile (v0=0, angle=90) | 高度 |
| 竖直上抛 | "竖直上抛"、"上抛" | projectile (angle=90) | 初速度 |
| 斜抛运动 | "抛体"、"弹道" | projectile | 初速度、角度 |
| 匀速直线 | "匀速" | uniform | 速度 |

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

## 故障排查

### OCR 无法识别文本

- 确保图片清晰
- 使用 `manual_text` 参数跳过 OCR：
  ```bash
  curl -X POST http://127.0.0.1:5000/upload -F "manual_text=题目内容"
  ```

### Claude API 调用失败

- 检查 `.env` 文件中的 `CLAUDE_API_KEY` 是否正确
- 查看后端日志，确认是否成功调用 API
- 如果 API 不可用，系统会自动降级使用规则引擎

### 动画不显示

- 打开浏览器控制台查看错误信息
- 确认后端返回的 `animation_instructions` 字段包含所需参数
- 检查 `type` 字段是否为 "projectile" 或 "uniform"

## Team Workflow

* Use `requirements.txt` for shared dependencies.
* Do NOT commit `.venv/` or `.env`.
* If you add a dependency:

  * `pip install <pkg>`
  * update `requirements.txt` (manual edit recommended for minimal deps, or `pip freeze > requirements.txt` if you prefer speed).

## License

Hackathon project.

