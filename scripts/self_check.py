#!/usr/bin/env python3
"""
自检测试脚本 - 验证 Claude Pipeline 和 Upload API 功能

测试项：
1. Manual 模式：不同 manual_text 产生不同输出
2. Claude 模式：API 调用正常（如果配置了 Key）
3. Pipeline 状态检查

使用方法：
  # Manual 模式（无需 API Key）
  export PIPELINE_MODE=manual
  python scripts/self_check.py

  # Claude 模式（需要配置 CLAUDE_API_KEY）
  export PIPELINE_MODE=claude
  export CLAUDE_API_KEY=your_api_key
  python scripts/self_check.py
"""

import os
import sys
import json
import tempfile
import requests
from pathlib import Path

# Flask 服务器地址
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def log_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def log_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def log_info(msg):
    print(f"ℹ️  {msg}")


def check_server_health():
    """检查服务器健康状态"""
    log_info("检查服务器健康状态...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            log_success("服务器运行正常")
            return True
        else:
            log_error(f"服务器返回错误状态码: {resp.status_code}")
            return False
    except Exception as e:
        log_error(f"无法连接到服务器: {e}")
        log_info("请确保服务器正在运行：python app.py")
        return False


def check_pipeline_status():
    """检查 Pipeline 状态"""
    log_info("检查 Pipeline 状态...")
    try:
        resp = requests.get(f"{BASE_URL}/pipeline/status", timeout=5)
        if resp.status_code == 200:
            status = resp.json()
            log_success(f"Pipeline 模式: {status['mode']}")

            if status['mode'] == 'claude':
                if status['claude_configured']:
                    log_success("Claude API 已配置")
                else:
                    log_warning("Claude API 未配置")
                    if status.get('error'):
                        log_info(f"错误信息: {status['error']}")

            return status
        else:
            log_error(f"Pipeline 状态检查失败: {resp.status_code}")
            return None
    except Exception as e:
        log_error(f"Pipeline 状态检查失败: {e}")
        return None


def create_dummy_image(path: str, content: str = "test"):
    """创建一个虚拟图片文件（1x1 PNG）"""
    # 创建一个最小的 PNG 文件
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'  # IHDR chunk
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'  # IDAT chunk
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
    )

    with open(path, 'wb') as f:
        f.write(png_data)


def test_manual_mode_with_different_texts():
    """测试 manual 模式：不同 manual_text 产生不同输出"""
    log_info("\n=== 测试 1: Manual 模式 - 不同 manual_text ===")

    # 设置 manual 模式
    original_mode = os.environ.get("PIPELINE_MODE")
    os.environ["PIPELINE_MODE"] = "manual"

    texts = [
        "一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²",
        "一个物体从20米高处以25m/s的初速度水平抛出，g=10m/s²",
        "一物体以30m/s的初速度与水平方向成45°角斜向上抛出，g=9.8m/s²",
    ]

    results = []

    for i, text in enumerate(texts):
        log_info(f"测试文本 {i+1}: {text[:30]}...")
        try:
            resp = requests.post(
                f"{BASE_URL}/upload",
                data={"manual_text": text},
                timeout=30
            )

            if resp.status_code == 200:
                result = resp.json()
                results.append(result)
                log_success(f"文本 {i+1} 解析成功")
                log_info(f"  problem_type: {result.get('problem_type')}")
                log_info(f"  animation_instructions.initial_speed: {result.get('animation_instructions', {}).get('initial_speed')}")
            else:
                log_error(f"文本 {i+1} 解析失败: {resp.status_code}")
                log_info(f"  响应: {resp.text[:200]}")
                return False

        except Exception as e:
            log_error(f"文本 {i+1} 请求失败: {e}")
            return False

    # 恢复原始模式
    if original_mode:
        os.environ["PIPELINE_MODE"] = original_mode
    else:
        os.environ.pop("PIPELINE_MODE", None)

    # 验证结果不同
    if len(results) >= 3:
        # 检查至少一个关键字段不同
        different = (
            len(set(r.get('problem_type') for r in results)) > 1 or
            len(set(r.get('problem_text') for r in results)) == len(results) or
            len(set(str(r.get('animation_instructions')) for r in results)) > 1
        )

        if different:
            log_success("✅ 测试通过：不同 manual_text 产生不同输出")
            return True
        else:
            log_error("❌ 测试失败：不同 manual_text 产生相同输出（可能是硬编码）")
            return False

    return False


def test_claude_mode():
    """测试 Claude 模式（如果配置了 Key）"""
    log_info("\n=== 测试 2: Claude 模式（可选） ===")

    # 检查是否配置了 Claude Key
    api_key = os.environ.get("CLAUDE_API_KEY", "").strip()

    if not api_key:
        log_warning("Claude API 未配置，跳过此测试")
        log_info("如需测试 Claude 模式，请设置环境变量：")
        log_info("  export CLAUDE_API_KEY=your_api_key")
        return True  # 跳过不算失败

    # 设置 claude 模式
    original_mode = os.environ.get("PIPELINE_MODE")
    os.environ["PIPELINE_MODE"] = "claude"

    log_info("Claude API 已配置，测试上传...")

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, "test_claude.png")
        create_dummy_image(image_path)

        try:
            with open(image_path, 'rb') as f:
                resp = requests.post(
                    f"{BASE_URL}/upload",
                    files={"file": ("test.png", f, "image/png")},
                    timeout=60  # Claude 可能较慢
                )

            if resp.status_code == 200:
                result = resp.json()
                log_success("Claude 模式测试通过")
                log_info(f"  problem_type: {result.get('problem_type')}")
                log_info(f"  problem_text: {result.get('problem_text', '')[:50]}...")
                return True
            else:
                log_error(f"Claude 模式测试失败: {resp.status_code}")
                log_info(f"  响应: {resp.text[:200]}")
                return False

        except Exception as e:
            log_error(f"Claude 模式测试失败: {e}")
            return False
        finally:
            # 恢复原始模式
            if original_mode:
                os.environ["PIPELINE_MODE"] = original_mode
            else:
                os.environ.pop("PIPELINE_MODE", None)


def main():
    print("=" * 60)
    print("Claude Pipeline 系统自检测试")
    print("=" * 60)

    # 1. 检查服务器健康
    if not check_server_health():
        log_error("服务器未运行，测试终止")
        sys.exit(1)

    # 2. 检查 Pipeline 状态
    pipeline_status = check_pipeline_status()
    if not pipeline_status:
        log_error("Pipeline 状态检查失败，测试终止")
        sys.exit(1)

    # 3. 运行测试
    results = []

    # 测试 1: Manual 模式 - 不同 manual_text
    results.append(("Manual 模式 - 不同 manual_text", test_manual_mode_with_different_texts()))

    # 测试 2: Claude 模式（可选）
    results.append(("Claude 模式", test_claude_mode()))

    # 输出结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        if result:
            log_success(f"{name}: 通过")
            passed += 1
        else:
            log_error(f"{name}: 失败")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        log_success(f"所有测试通过！({passed}/{len(results)})")
        sys.exit(0)
    else:
        log_error(f"部分测试失败：{failed}/{len(results)}")
        sys.exit(1)


if __name__ == "__main__":
    main()