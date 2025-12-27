# 动态输出修复总结

## 问题描述

用户报告上传不同图片时总是返回相同的解题步骤和动画指令，导致 UI 和 Canvas 动画永不改变。

## 根本原因分析

经过全面审计，发现：

1. **代码库中没有硬编码的响应** - 系统已经正确设计为动态分析
2. **数据流是正确的**：上传 → OCR → LLM/规则引擎 → 构建响应
3. **实际问题**：规则引擎的参数提取和运动类型分类存在 bug，导致某些情况下提取不准确

## 修复内容

### 1. 改进参数提取正则表达式 (services/llm_service.py:201-235)

**问题**：`_extract_parameters_fallback()` 无法正确提取某些格式的速度和高度参数

**修复**：添加更多正则模式以覆盖常见的中文物理题表述

```python
# 新增的速度提取模式
r"以\s*([0-9]+(?:\.[0-9]+)?)\s*m/s",
r"([0-9]+(?:\.[0-9]+)?)\s*m/s\s*的.*速度",

# 新增的角度提取模式
r"([0-9]+(?:\.[0-9]+)?)\s*[°度]\s*角",
r"以\s*([0-9]+(?:\.[0-9]+)?)\s*[°度]",

# 新增的高度提取模式
r"([0-9]+(?:\.[0-9]+)?)\s*米高",
r"([0-9]+(?:\.[0-9]+)?)\s*m高",
```

**测试结果**：
- ✅ "以 25 m/s 的初速度" → 正确提取 speed=25.0
- ✅ "从 10 米高的平台" → 正确提取 height=10.0
- ✅ "以 60° 角" → 正确提取 angle=60.0

### 2. 优化运动类型分类逻辑 (services/llm_service.py:238-289)

**问题**：`_detect_motion_type_fallback()` 将"斜向上抛"误判为"竖直上抛"

**修复**：重构分类逻辑，按优先级排序：

1. 先检查明确的类型（匀速、自由落体、平抛）
2. 竖直上抛只匹配明确包含"竖直"的情况
3. 通过角度值辅助判断（0° → 平抛，90° → 竖直，其他 → 斜抛）
4. 检查"斜"、"角度"等关键词
5. 最后才检查一般的"抛"

**测试结果**：
- ✅ 平抛运动：`horizontal_projectile`
- ✅ 自由落体：`free_fall`
- ✅ 斜抛运动（60°）：`projectile` *(之前误判为 vertical_throw)*
- ✅ 匀速直线：`uniform`

### 3. 确认系统架构无硬编码问题

经审计确认：

✅ **OCR 服务** (`services/ocr_service.py`)
- 正确从图片提取文本（PaddleOCR）
- Mock 模式仅用于测试，默认使用真实 OCR

✅ **LLM 服务** (`services/llm_service.py`)
- 支持 Claude API 和规则引擎双模式
- 规则引擎基于 OCR 文本动态提取参数和分类

✅ **上传路由** (`routes/upload.py`)
- 正确调用 OCR → LLM → 构建响应
- 支持 `manual_text` 参数用于测试

✅ **JSON 构建器** (`utils/json_builder.py`)
- 简单的结构化封装，无硬编码数据

✅ **前端** (`static/main.js`)
- 正确读取 `solution_steps` 和 `animation_instructions`
- 已兼容新旧字段名

### 4. 添加回归测试

创建了两个测试脚本：

#### a) 单元测试 (`scripts/test_dynamic_response.py`)

测试 LLM 服务的参数提取和分类功能：

```bash
python scripts/test_dynamic_response.py
```

**验证项**：
- 4 种不同运动类型的 OCR 文本
- 所有 `solution_steps` 必须不同
- 所有 `motion_type` 分类必须正确

#### b) 端到端测试 (`scripts/test_upload_endpoint.py`)

测试完整的上传接口：

```bash
# 先启动 Flask 应用
python app.py

# 在另一个终端运行测试
python scripts/test_upload_endpoint.py
```

**验证项**：
- 响应包含所有必需字段
- 不同输入产生不同 `solution_steps`
- 不同输入产生不同 `animation_instructions`
- `problem_type` 正确分类

## 修改的文件

1. **services/llm_service.py** (修复)
   - 改进 `_extract_parameters_fallback()` 正则表达式
   - 重构 `_detect_motion_type_fallback()` 分类逻辑

2. **scripts/test_dynamic_response.py** (新增)
   - 单元测试：验证参数提取和分类

3. **scripts/test_upload_endpoint.py** (新增)
   - 端到端测试：验证上传接口动态输出

4. **DYNAMIC_OUTPUT_FIX_SUMMARY.md** (本文档)
   - 修复总结和使用说明

## 验证步骤

### 方式 1：自动化测试

```bash
# 单元测试（无需启动服务）
python scripts/test_dynamic_response.py

# 端到端测试（需要启动服务）
python app.py &
python scripts/test_upload_endpoint.py
```

### 方式 2：手动测试

1. 启动应用：
   ```bash
   python app.py
   ```

2. 使用 `manual_text` 参数测试：
   ```bash
   # 测试平抛运动
   curl -X POST http://127.0.0.1:5000/upload \
     -F 'manual_text=一小球以 15 m/s 的初速度水平抛出，从 10 米高的平台'

   # 测试自由落体
   curl -X POST http://127.0.0.1:5000/upload \
     -F 'manual_text=一物体从 20 米高处自由落体'

   # 测试斜抛运动
   curl -X POST http://127.0.0.1:5000/upload \
     -F 'manual_text=以 25 m/s 的初速度以 60° 角斜向上抛出'
   ```

3. 验证每个请求返回不同的：
   - `solution_steps`
   - `animation_instructions`
   - `problem_type`

### 方式 3：浏览器测试

1. 访问 `http://127.0.0.1:5000/`
2. 上传不同的物理题图片（或使用开发者工具手动构造 FormData）
3. 观察控制台输出和动画效果是否随图片变化

## 技术细节

### LLM 模式切换

系统支持两种模式：

1. **Claude API 模式**（推荐，更准确）
   - 需要配置 `CLAUDE_API_KEY`
   - 自动生成结构化 JSON 输出

2. **规则引擎模式**（降级方案）
   - 无需 API Key
   - 使用正则表达式提取参数
   - 本次修复重点改进了此模式

### 响应结构保证

所有响应必须包含：

```json
{
  "problem_type": "physics_<motion_type>",
  "ocr_text": "识别的文本",
  "solution_steps": [
    "步骤1",
    "步骤2",
    ...
  ],
  "animation_instructions": {
    "type": "projectile|uniform",
    "initial_speed": 20.0,
    "angle": 45.0,
    "gravity": 9.8,
    "initial_x": 0,
    "initial_y": 0,
    "duration": 4.5,
    "scale": 24
  },
  "parameters": {
    "motion_type": "horizontal_projectile|free_fall|vertical_throw|projectile|uniform",
    ...
  }
}
```

## 环境配置

### 不使用 Claude API（规则引擎）

```.env
# 不设置 CLAUDE_API_KEY，或设置为空
CLAUDE_API_KEY=

# OCR 使用 PaddleOCR（默认）
OCR_PROVIDER=paddle
```

### 使用 Claude API（推荐）

```.env
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=2048

OCR_PROVIDER=paddle
```

## 安全性

- ✅ 不提交 API Key 到代码库（使用环境变量）
- ✅ `.env` 文件已在 `.gitignore` 中
- ✅ 配置示例使用 `.env.example`

## 向后兼容性

- ✅ 前端同时支持 `solution_steps` 和旧的 `steps` 字段
- ✅ 响应结构保持稳定
- ✅ 规则引擎作为 LLM 的降级方案

## 性能优化

- OCR 引擎使用单例模式，避免重复加载模型
- 支持 `manual_text` 参数跳过 OCR（调试用）
- LLM 失败时自动降级到规则引擎

## 已知限制

1. **规则引擎准确性**：对于复杂或非标准表述的题目，规则引擎可能提取不准
   - 建议：配置 Claude API 以获得最佳效果

2. **OCR 准确性**：PaddleOCR 对模糊或手写图片识别率较低
   - 解决方案：使用 `manual_text` 参数手动输入文本

## 下一步优化建议

1. 添加更多测试用例（复杂题目、边界情况）
2. 改进规则引擎的数值单位处理（如 km/h、cm 等）
3. 支持更多运动类型（圆周运动、斜面运动等）
4. 添加前端实时预览和参数编辑功能

## 结论

系统**没有硬编码问题**，已经正确实现动态分析。本次修复主要**改进了规则引擎的准确性**，使其能够正确提取参数和分类运动类型。

所有测试通过，不同输入现在产生不同的 `solution_steps` 和 `animation_instructions`。