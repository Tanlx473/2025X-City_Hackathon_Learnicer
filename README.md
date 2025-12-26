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

### 2) Install PaddlePaddle (macOS / Apple Silicon recommended)

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

```bash
pip install -r requirements.txt
```

## Known Issue (Python 3.13 + PaddleOCR Import Error)

On Python 3.13, `import paddleocr` may fail due to a transitive dependency (`modelscope`) expecting `HUB_DATASET_ENDPOINT` to be set.

Workaround: set the env var before importing PaddleOCR:

Option A — set in code (recommended in backend entrypoint):

```python
import os
os.environ.setdefault("HUB_DATASET_ENDPOINT", "https://modelscope.cn/api/v1/datasets")
```

Option B — set in shell:

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

## Team Workflow

* Use `requirements.txt` for shared dependencies.
* Do NOT commit `.venv/` or `.env`.
* If you add a dependency:

  * `pip install <pkg>`
  * update `requirements.txt` (manual edit recommended for minimal deps, or `pip freeze > requirements.txt` if you prefer speed).

## License

Hackathon project.

