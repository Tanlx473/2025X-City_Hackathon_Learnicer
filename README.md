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


## Team Workflow

* Use `requirements.txt` for shared dependencies.
* Do NOT commit `.venv/` or `.env`.
* If you add a dependency:

  * `pip install <pkg>`
  * update `requirements.txt` (manual edit recommended for minimal deps, or `pip freeze > requirements.txt` if you prefer speed).

## License

Hackathon project.

