#!/usr/bin/env python3
"""
快速测试脚本 - 验证 OCR 服务逻辑（不需要启动 Flask）

直接测试 services/ocr_service.py 的功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.ocr_service import extract_text, get_ocr_status


def create_dummy_image(path: str):
    """创建一个虚拟图片文件（1x1 PNG）"""
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    with open(path, 'wb') as f:
        f.write(png_data)


def test_ocr_status():
    """测试 OCR 状态检查"""
    print("\n=== 测试 OCR 状态 ===")
    status = get_ocr_status()
    print(f"OCR 模式: {status['mode']}")
    print(f"Mathpix 配置: {status['mathpix_configured']}")
    if status.get('error'):
        print(f"错误: {status['error']}")
    print("✅ OCR 状态检查通过")


def test_manual_mode_with_text():
    """测试 manual 模式 - 使用 manual_text"""
    print("\n=== 测试 1: Manual 模式 - 使用 manual_text ===")

    # 设置 manual 模式
    os.environ["OCR_MODE"] = "manual"

    texts = [
        "一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²",
        "一个物体从20米高处以25m/s的初速度水平抛出，g=10m/s²",
    ]

    results = []
    for i, text in enumerate(texts):
        print(f"\n测试文本 {i+1}: {text[:30]}...")
        result = extract_text("placeholder.jpg", manual_text=text)
        print(f"结果长度: {len(result)} 字符")
        print(f"结果预览: {result[:100]}...")
        results.append(result)

    # 验证结果不同
    if results[0] != results[1]:
        print("\n✅ 测试通过：不同 manual_text 产生不同输出")
        return True
    else:
        print("\n❌ 测试失败：不同 manual_text 产生相同输出")
        return False


def test_manual_mode_with_images():
    """测试 manual 模式 - 使用不同图片"""
    print("\n=== 测试 2: Manual 模式 - 使用不同图片 ===")

    # 设置 manual 模式
    os.environ["OCR_MODE"] = "manual"

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(2):
            # 创建不同的图片文件
            image_path = os.path.join(tmpdir, f"test_{i}.png")
            create_dummy_image(image_path)

            print(f"\n测试图片 {i+1}: {os.path.basename(image_path)}")
            result = extract_text(image_path, manual_text=None)
            print(f"结果长度: {len(result)} 字符")
            print(f"结果预览: {result[:100]}...")
            results.append(result)

    # 验证结果不同
    if results[0] != results[1]:
        print("\n✅ 测试通过：不同图片产生不同输出")
        return True
    else:
        print("\n❌ 测试失败：不同图片产生相同输出")
        return False


def test_manual_mode_deterministic():
    """测试 manual 模式 - 确定性（相同输入产生相同输出）"""
    print("\n=== 测试 3: Manual 模式 - 确定性 ===")

    # 设置 manual 模式
    os.environ["OCR_MODE"] = "manual"

    text = "一个物体从10米高处以15m/s的初速度水平抛出，g=9.8m/s²"

    result1 = extract_text("placeholder.jpg", manual_text=text)
    result2 = extract_text("placeholder.jpg", manual_text=text)

    if result1 == result2:
        print("\n✅ 测试通过：相同输入产生相同输出（确定性）")
        return True
    else:
        print("\n❌ 测试失败：相同输入产生不同输出（非确定性）")
        return False


def main():
    print("=" * 60)
    print("OCR 服务快速测试（无需启动 Flask）")
    print("=" * 60)

    # OCR 状态检查
    test_ocr_status()

    # 运行测试
    results = []
    results.append(("Manual 模式 - manual_text", test_manual_mode_with_text()))
    results.append(("Manual 模式 - 不同图片", test_manual_mode_with_images()))
    results.append(("Manual 模式 - 确定性", test_manual_mode_deterministic()))

    # 输出摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"✅ 所有测试通过！({passed}/{len(results)})")
        return 0
    else:
        print(f"❌ 部分测试失败：{failed}/{len(results)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())