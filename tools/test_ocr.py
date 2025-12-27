#!/usr/bin/env python3
"""
OCR 冒烟测试脚本

用于快速验证 OCR 服务是否正常工作

使用方法：
    python tools/test_ocr.py [image_path]

示例：
    # 测试真实图片
    python tools/test_ocr.py test_images/physics_problem.jpg

    # 测试 mock 模式
    OCR_PROVIDER=mock python tools/test_ocr.py test_images/physics_problem.jpg

    # 无图片时也能测试（mock模式）
    OCR_PROVIDER=mock python tools/test_ocr.py
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def print_header(text: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60 + "\n")


def print_section(text: str):
    """打印小节"""
    print(f"\n--- {text} ---\n")


def test_ocr(image_path: str = None):
    """
    测试 OCR 服务

    Args:
        image_path: 图片路径（可选，如果不提供且使用 mock 模式仍可测试）
    """
    from services.ocr_service import extract_text, get_ocr_provider, get_ocr_status

    print_header("OCR 服务测试")

    # 1. 显示配置
    print_section("1. 当前配置")
    provider = get_ocr_provider()
    print(f"OCR Provider: {provider}")
    print(f"OCR Language: {os.getenv('OCR_LANG', 'ch')}")

    # 2. 检查状态
    print_section("2. 状态检查")
    status = get_ocr_status()
    print(f"Provider: {status['provider']}")
    print(f"Initialized: {status['initialized']}")
    print(f"Language: {status['lang']}")
    if status['error']:
        print(f"⚠️  Error: {status['error']}")
    else:
        print("✅ OCR 引擎初始化正常")

    # 3. 测试 OCR 提取
    print_section("3. OCR 文本提取")

    if not image_path and provider != "mock":
        print("⚠️  未提供图片路径")
        print("   使用方法：python tools/test_ocr.py <image_path>")
        print("   或使用 mock 模式：OCR_PROVIDER=mock python tools/test_ocr.py")
        return

    # 对于 mock 模式，即使没有图片也能测试
    if provider == "mock" and not image_path:
        image_path = "dummy.jpg"  # mock 模式不会真正读取文件

    try:
        print(f"正在处理图片: {image_path}")

        start_time = time.time()
        text = extract_text(image_path)
        elapsed = time.time() - start_time

        print(f"\n✅ OCR 成功！")
        print(f"   耗时: {elapsed:.2f} 秒")
        print(f"   文本长度: {len(text)} 字符")

        # 显示识别结果
        print_section("4. 识别结果")
        if len(text) > 500:
            print(text[:500] + "\n... (截断，完整文本较长)")
        else:
            print(text)

        # 显示统计信息
        print_section("5. 统计信息")
        lines = [line for line in text.split('\n') if line.strip()]
        print(f"行数: {len(lines)}")
        print(f"字符数: {len(text)}")
        print(f"平均每行字符数: {len(text) / max(len(lines), 1):.1f}")

        # 检查关键词（物理题常见术语）
        keywords = ['速度', '加速度', '重力', 'm/s', 'g =', '初速度', '抛出', '落地']
        found_keywords = [kw for kw in keywords if kw in text]
        if found_keywords:
            print(f"\n检测到物理关键词: {', '.join(found_keywords)}")

        return True

    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        return False

    except Exception as e:
        print(f"\n❌ OCR 失败: {e}")
        print(f"\n建议：")
        print(f"1. 检查图片文件是否存在且可读")
        print(f"2. 如果 PaddleOCR 未安装，使用 mock 模式：")
        print(f"   export OCR_PROVIDER=mock")
        print(f"3. 或使用 manual 模式手动输入文本")
        return False


def main():
    """主函数"""
    image_path = None

    if len(sys.argv) > 1:
        image_path = sys.argv[1]

        # 检查文件是否存在
        provider = os.getenv("OCR_PROVIDER", "paddle").lower()
        if provider != "mock" and not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            print("\n提示：")
            print("1. 请提供正确的图片路径")
            print("2. 或使用 mock 模式测试：OCR_PROVIDER=mock python tools/test_ocr.py")
            sys.exit(1)

    # 运行测试
    success = test_ocr(image_path)

    # 输出测试结果
    print_header("测试结果")
    if success:
        print("✅ 所有测试通过！")
        print("\n下一步：")
        print("1. 启动后端服务：python app.py")
        print("2. 测试上传接口：curl -X POST http://127.0.0.1:5000/upload -F 'file=@test.jpg'")
        print("3. 或使用 manual_text：curl -X POST http://127.0.0.1:5000/upload -F 'file=@test.jpg' -F 'manual_text=题目文本'")
    else:
        print("❌ 测试失败")
        print("\n请检查上方的错误信息并修复")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()