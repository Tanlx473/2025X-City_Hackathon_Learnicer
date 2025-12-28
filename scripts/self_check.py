#!/usr/bin/env python3
"""
自检测试脚本 - 验证 OCR 和 Upload API 功能

测试项：
1. Manual 模式：不同 manual_text 产生不同输出
2. Manual 模式：不同图片产生不同输出（自动生成）
3. Mathpix 模式：API 调用正常（如果配置了 Key）
4. OCR 状态检查

使用方法：
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


def check_ocr_status():
    """检查 OCR 状态"""
    log_info("检查 OCR 状态...")
    try:
        resp = requests.get(f"{BASE_URL}/ocr/status", timeout=5)
        if resp.status_code == 200:
            status = resp.json()
            log_success(f"OCR 模式: {status['mode']}")

            if status['mode'] == 'mathpix':
                if status['mathpix_configured']:
                    log_success("Mathpix API 已配置")
                else:
                    log_warning("Mathpix API 未配置")
                    if status.get('error'):
                        log_info(f"错误信息: {status['error']}")

            return status
        else:
            log_error(f"OCR 状态检查失败: {resp.status_code}")
            return None
    except Exception as e:
        log_error(f"OCR 状态检查失败: {e}")
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
    original_mode = os.environ.get("OCR_MODE")
    os.environ["OCR_MODE"] = "manual"

    texts = [
        "一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²",
        "一个物体从20米高处以25m/s的初速度水平抛出，g=10m/s²",
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
            else:
                log_error(f"文本 {i+1} 解析失败: {resp.status_code}")
                log_info(f"  响应: {resp.text[:200]}")
                return False

        except Exception as e:
            log_error(f"文本 {i+1} 请求失败: {e}")
            return False

    # 恢复原始模式
    if original_mode:
        os.environ["OCR_MODE"] = original_mode
    else:
        os.environ.pop("OCR_MODE", None)

    # 验证结果不同
    if len(results) >= 2:
        # 检查至少一个关键字段不同
        different = (
            results[0].get('problem_type') != results[1].get('problem_type') or
            results[0].get('problem_text') != results[1].get('problem_text') or
            results[0].get('animation_instructions') != results[1].get('animation_instructions')
        )

        if different:
            log_success("✅ 测试通过：不同 manual_text 产生不同输出")
            return True
        else:
            log_error("❌ 测试失败：不同 manual_text 产生相同输出（可能是硬编码）")
            return False

    return False


def test_manual_mode_with_different_images():
    """测试 manual 模式：不同图片产生不同输出"""
    log_info("\n=== 测试 2: Manual 模式 - 不同图片（自动生成） ===")

    # 设置 manual 模式
    original_mode = os.environ.get("OCR_MODE")
    os.environ["OCR_MODE"] = "manual"

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(2):
            # 创建不同的图片文件
            image_path = os.path.join(tmpdir, f"test_{i}.png")
            create_dummy_image(image_path, content=f"test_{i}")

            log_info(f"测试图片 {i+1}: {image_path}")

            try:
                with open(image_path, 'rb') as f:
                    resp = requests.post(
                        f"{BASE_URL}/upload",
                        files={"file": (f"test_{i}.png", f, "image/png")},
                        timeout=30
                    )

                if resp.status_code == 200:
                    result = resp.json()
                    results.append(result)
                    log_success(f"图片 {i+1} 解析成功")
                    log_info(f"  problem_type: {result.get('problem_type')}")
                else:
                    log_error(f"图片 {i+1} 解析失败: {resp.status_code}")
                    log_info(f"  响应: {resp.text[:200]}")
                    return False

            except Exception as e:
                log_error(f"图片 {i+1} 请求失败: {e}")
                return False

    # 恢复原始模式
    if original_mode:
        os.environ["OCR_MODE"] = original_mode
    else:
        os.environ.pop("OCR_MODE", None)

    # 验证结果不同
    if len(results) >= 2:
        different = (
            results[0].get('problem_text') != results[1].get('problem_text') or
            results[0].get('animation_instructions') != results[1].get('animation_instructions')
        )

        if different:
            log_success("✅ 测试通过：不同图片产生不同输出")
            return True
        else:
            log_error("❌ 测试失败：不同图片产生相同输出")
            log_info("可能原因：图片 hash 生成逻辑有问题")
            return False

    return False


def test_mathpix_mode():
    """测试 Mathpix 模式（如果配置了 Key）"""
    log_info("\n=== 测试 3: Mathpix 模式（可选） ===")

    # 检查是否配置了 Mathpix Key
    app_id = os.environ.get("MATHPIX_APP_ID", "").strip()
    app_key = os.environ.get("MATHPIX_APP_KEY", "").strip()

    if not app_id or not app_key:
        log_warning("Mathpix API 未配置，跳过此测试")
        log_info("如需测试 Mathpix 模式，请设置环境变量：")
        log_info("  export MATHPIX_APP_ID=your_app_id")
        log_info("  export MATHPIX_APP_KEY=your_app_key")
        return True  # 跳过不算失败

    # 设置 mathpix 模式
    original_mode = os.environ.get("OCR_MODE")
    os.environ["OCR_MODE"] = "mathpix"

    log_info("Mathpix API 已配置，测试上传...")

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, "test_mathpix.png")
        create_dummy_image(image_path)

        try:
            with open(image_path, 'rb') as f:
                resp = requests.post(
                    f"{BASE_URL}/upload",
                    files={"file": ("test.png", f, "image/png")},
                    timeout=60  # Mathpix 可能较慢
                )

            if resp.status_code == 200:
                result = resp.json()
                log_success("Mathpix 模式测试通过")
                log_info(f"  problem_type: {result.get('problem_type')}")
                return True
            else:
                log_error(f"Mathpix 模式测试失败: {resp.status_code}")
                log_info(f"  响应: {resp.text[:200]}")
                return False

        except Exception as e:
            log_error(f"Mathpix 模式测试失败: {e}")
            return False
        finally:
            # 恢复原始模式
            if original_mode:
                os.environ["OCR_MODE"] = original_mode
            else:
                os.environ.pop("OCR_MODE", None)


def main():
    print("=" * 60)
    print("OCR 系统自检测试")
    print("=" * 60)

    # 1. 检查服务器健康
    if not check_server_health():
        log_error("服务器未运行，测试终止")
        sys.exit(1)

    # 2. 检查 OCR 状态
    ocr_status = check_ocr_status()
    if not ocr_status:
        log_error("OCR 状态检查失败，测试终止")
        sys.exit(1)

    # 3. 运行测试
    results = []

    # 测试 1: Manual 模式 - 不同 manual_text
    results.append(("Manual 模式 - 不同 manual_text", test_manual_mode_with_different_texts()))

    # 测试 2: Manual 模式 - 不同图片
    results.append(("Manual 模式 - 不同图片", test_manual_mode_with_different_images()))

    # 测试 3: Mathpix 模式（可选）
    results.append(("Mathpix 模式", test_mathpix_mode()))

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