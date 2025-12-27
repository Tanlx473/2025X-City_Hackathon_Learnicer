# OCR 集成使用指南

## 📋 概述

本项目使用 **Paddle OCR** 从物理题目图片中提取文本，支持多种 OCR provider 切换，确保在不同环境下都能正常演示。

---

## 🔧 OCR Provider 配置

通过环境变量 `OCR_PROVIDER` 控制使用哪种 OCR 实现：

### 1. PaddleOCR（默认，生产环境推荐）

```bash
export OCR_PROVIDER=paddle
# 或在 .env 文件中设置
OCR_PROVIDER=paddle
```

**特点**：
- ✅ 识别准确率高
- ✅ 支持中英混合
- ⚠️ 需要安装 `paddleocr` 和 `paddlepaddle`
- ⚠️ 首次运行会下载模型文件（约 20MB）

**安装方法**：
```bash
# macOS (ARM64, M系列芯片)
python3 -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# 验证安装
python -c "import paddle; paddle.utils.run_check()"

# 安装 PaddleOCR
pip install paddleocr
```

---

### 2. Mock OCR（快速测试，无需安装）

```bash
export OCR_PROVIDER=mock
```

**特点**：
- ✅ 无需安装 PaddleOCR
- ✅ 立即可用，用于演示
- ✅ 返回预设的物理题文本（平抛运动）
- ⚠️ 不支持真实图片识别

**适用场景**：
- PaddleOCR 安装失败或不可用时
- 快速测试后端 LLM 链路
- Demo 演示

---

### 3. Manual OCR（手动输入）

```bash
export OCR_PROVIDER=manual
```

**特点**：
- ✅ 完全手动控制
- ✅ 通过 `manual_text` 参数提供文本
- ⚠️ 每次请求都需要提供 `manual_text`

**使用方法**：
```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test.jpg" \
  -F "manual_text=一小球以 20 m/s 的初速度从地面以 45° 角斜向上抛出..."
```

---

## 🧪 测试 OCR 功能

### 方式 1：使用测试脚本（推荐）

```bash
# 测试 PaddleOCR（默认）
python tools/test_ocr.py test_images/physics_problem.jpg

# 测试 Mock OCR
OCR_PROVIDER=mock python tools/test_ocr.py

# 无图片时测试 Mock OCR
OCR_PROVIDER=mock python tools/test_ocr.py
```

**测试脚本输出**：
- OCR provider 配置
- 初始化状态
- 提取的文本内容
- 识别耗时
- 统计信息（行数、字符数、关键词）

---

### 方式 2：使用健康检查接口

```bash
# 启动服务器
python app.py

# 检查 OCR 状态
curl http://127.0.0.1:5000/ocr/status
```

**返回示例**：
```json
{
  "provider": "paddle",
  "initialized": true,
  "lang": "ch",
  "error": null
}
```

---

### 方式 3：测试完整上传流程

```bash
# 1. 真实图片 OCR
curl -X POST http://127.0.0.1:5000/upload -F "file=@test_images/physics.jpg"

# 2. Mock OCR（无需图片）
OCR_PROVIDER=mock curl -X POST http://127.0.0.1:5000/upload -F "file=@dummy.jpg"

# 3. Manual OCR（手动输入）
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@test.jpg" \
  -F "manual_text=一小球以 20 m/s..."
```

---

## ⚙️ 配置详解

### 环境变量

在 `.env` 文件中配置：

```bash
# OCR Provider（默认 paddle）
OCR_PROVIDER=paddle  # 可选值：paddle, mock, manual

# OCR 语言（默认 ch）
OCR_LANG=ch  # 可选值：ch（中英混合）, en（仅英文）

# PaddleOCR 兼容性（Python 3.13+）
HUB_DATASET_ENDPOINT=https://modelscope.cn/api/v1/datasets
```

### 代码层配置（config.py）

```python
class Config:
    # OCR 语言设置
    OCR_LANG = "ch"  # 支持中英混合

    # 允许的图片格式
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # 上传文件大小限制
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
```

---

## 🐛 常见问题

### 问题 1：PaddleOCR 导入失败

**错误信息**：
```
ImportError: No module named 'paddleocr'
```

**解决方案**：
```bash
# 先安装 paddlepaddle
python3 -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# 再安装 paddleocr
pip install paddleocr

# 或使用 mock 模式绕过
export OCR_PROVIDER=mock
```

---

### 问题 2：PaddleOCR 初始化失败

**错误信息**：
```
RuntimeError: PaddleOCR 初始化失败
```

**解决方案**：
```bash
# 方案 1：检查 PaddlePaddle 是否正确安装
python -c "import paddle; paddle.utils.run_check()"

# 方案 2：使用 mock 模式
export OCR_PROVIDER=mock

# 方案 3：使用 manual 模式
export OCR_PROVIDER=manual
```

---

### 问题 3：OCR 未识别到文本

**错误信息**：
```json
{
  "error": "ocr_no_text",
  "message": "未能从图片中识别到文本"
}
```

**解决方案**：
1. 确保图片清晰且包含文字
2. 尝试调整图片分辨率（建议 >= 800px）
3. 使用 `manual_text` 参数手动输入：
   ```bash
   curl -X POST http://127.0.0.1:5000/upload \
     -F "file=@test.jpg" \
     -F "manual_text=题目文本内容..."
   ```

---

### 问题 4：macOS x86_64 不支持

**错误信息**：
```
PaddlePaddle on macOS only supports ARM64 (M series)
```

**解决方案**：
- macOS Intel 芯片不再被 PaddlePaddle 3.x 支持
- 使用 mock 或 manual 模式：
  ```bash
  export OCR_PROVIDER=mock
  ```

---

## 📊 性能优化

### 1. 全局单例缓存

OCR 引擎使用全局单例模式，避免重复加载模型：

```python
# services/ocr_service.py
_ocr = None  # 全局单例

def get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(...)  # 仅首次初始化
    return _ocr
```

### 2. 懒加载

OCR 引擎在首次使用时才初始化，不影响应用启动速度。

### 3. 模型缓存

PaddleOCR 模型文件会自动缓存到本地：
```
~/.paddleocr/
```

---

## 🔄 切换 OCR Provider

### 临时切换（单次测试）

```bash
# 使用 mock 模式测试
OCR_PROVIDER=mock python app.py

# 使用 manual 模式测试
OCR_PROVIDER=manual python app.py
```

### 永久切换（修改 .env）

```bash
# 编辑 .env 文件
vi .env

# 修改 OCR_PROVIDER
OCR_PROVIDER=mock  # 或 paddle, manual
```

---

## 📖 API 参考

### extract_text(image_path, manual_text=None)

从图片中提取文本。

**参数**：
- `image_path` (str): 图片文件路径
- `manual_text` (str, 可选): 手动输入的文本（优先级最高）

**返回**：
- `str`: 提取的文本字符串

**异常**：
- `RuntimeError`: OCR 初始化或识别失败
- `FileNotFoundError`: 图片文件不存在
- `ValueError`: provider 不支持或参数错误

**示例**：
```python
from services.ocr_service import extract_text

# 使用 PaddleOCR
text = extract_text("test.jpg")

# 使用 manual_text 降级
text = extract_text("test.jpg", manual_text="题目文本...")
```

---

### get_ocr_status()

获取 OCR 状态信息。

**返回**：
```python
{
    "provider": "paddle/mock/manual",
    "initialized": bool,
    "lang": "ch/en",
    "error": Optional[str]
}
```

**示例**：
```python
from services.ocr_service import get_ocr_status

status = get_ocr_status()
print(f"Provider: {status['provider']}")
print(f"Initialized: {status['initialized']}")
```

---

## 🎯 最佳实践

### 开发环境

```bash
# 使用 mock 模式，快速测试 LLM 链路
export OCR_PROVIDER=mock
python app.py
```

### 生产环境

```bash
# 使用 PaddleOCR，获得最佳识别效果
export OCR_PROVIDER=paddle
export OCR_LANG=ch
python app.py
```

### 演示环境

```bash
# 使用 mock 或 manual，避免依赖 PaddleOCR
export OCR_PROVIDER=mock
python app.py
```

---

## 🚀 下一步

OCR 功能验证通过后，可以继续：

1. **测试完整流程**：
   ```bash
   curl -X POST http://127.0.0.1:5000/upload -F "file=@test.jpg"
   ```

2. **集成前端**：
   - 访问 http://127.0.0.1:5000/
   - 上传物理题图片
   - 查看 OCR + LLM + 动画结果

3. **优化识别**：
   - 调整图片分辨率
   - 使用更清晰的图片
   - 尝试不同的 OCR_LANG 设置

---

## 📞 问题反馈

如遇到其他问题，请：
1. 检查 `tools/test_ocr.py` 的输出
2. 查看后端日志（`python app.py` 的控制台输出）
3. 访问 `/ocr/status` 接口查看 OCR 状态