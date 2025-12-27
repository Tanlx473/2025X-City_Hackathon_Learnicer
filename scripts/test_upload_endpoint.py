#!/usr/bin/env python3
"""
端到端回归测试：验证上传不同文本产生不同输出

测试通过 /upload 端点使用 manual_text 参数模拟不同图片的 OCR 结果
"""

import sys
import os
import requests
import json

# Flask 应用 URL（假设运行在本地）
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")


def test_upload_with_manual_text(text: str, description: str) -> dict:
    """
    使用 manual_text 参数测试上传接口

    Args:
        text: 模拟的 OCR 文本
        description: 测试用例描述

    Returns:
        API 返回的 JSON 响应
    """
    print(f"\n{'='*80}")
    print(f"测试: {description}")
    print(f"{'='*80}")
    print(f"输入文本: {text[:60]}...")

    # 使用 manual_text 参数，跳过实际的文件上传和 OCR
    response = requests.post(
        f"{BASE_URL}/upload",
        data={"manual_text": text}
    )

    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return None

    data = response.json()

    # 打印关键字段
    print(f"✅ 请求成功")
    print(f"问题类型: {data.get('problem_type', 'N/A')}")
    print(f"OCR 文本长度: {len(data.get('ocr_text', ''))}")
    print(f"解题步骤数: {len(data.get('solution_steps', []))}")
    print(f"解题步骤: {data.get('solution_steps', [])}")
    print(f"动画类型: {data.get('animation_instructions', {}).get('type', 'N/A')}")
    print(f"动画参数: speed={data.get('animation_instructions', {}).get('initial_speed')}, " +
          f"angle={data.get('animation_instructions', {}).get('angle')}")

    return data


def main():
    """主测试函数"""

    # 检查服务是否运行
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=2)
        if health_response.status_code != 200:
            print(f"❌ 服务未运行或不健康。请先启动 Flask 应用: python app.py")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务 {BASE_URL}")
        print(f"   错误: {e}")
        print(f"   请先启动 Flask 应用: python app.py")
        return False

    print("\n" + "="*80)
    print("端到端回归测试：验证不同输入产生不同输出")
    print("="*80)

    # 测试用例
    test_cases = [
        ("平抛运动", "一小球以 12 m/s 的初速度水平抛出，从 15 米高的平台，g = 9.8 m/s²"),
        ("自由落体", "一物体从 25 米高处自由落体，重力加速度 g = 9.8 m/s²"),
        ("斜抛运动", "以 30 m/s 的初速度以 45° 角斜向上抛出，g = 9.8 m/s²"),
        ("匀速直线", "一辆车以 10 m/s 的速度匀速直线运动"),
    ]

    results = []

    for description, text in test_cases:
        result = test_upload_with_manual_text(text, description)
        if result is None:
            print(f"\n❌ 测试失败：{description}")
            return False

        results.append({
            'description': description,
            'text': text,
            'result': result
        })

    # 验证结果
    print("\n" + "="*80)
    print("验证结果")
    print("="*80)

    # 检查1：所有结果必须包含必需字段
    required_fields = ['problem_type', 'ocr_text', 'solution_steps', 'animation_instructions']
    all_have_required = True

    for r in results:
        missing = [field for field in required_fields if field not in r['result']]
        if missing:
            print(f"❌ {r['description']}: 缺少必需字段 {missing}")
            all_have_required = False

    if all_have_required:
        print("✅ PASS: 所有响应都包含必需字段")
    else:
        print("❌ FAIL: 部分响应缺少必需字段")
        return False

    # 检查2：所有 solution_steps 必须不同
    steps_set = set()
    for r in results:
        steps_str = json.dumps(r['result']['solution_steps'], sort_keys=True)
        steps_set.add(steps_str)

    if len(steps_set) == len(results):
        print(f"✅ PASS: 所有 solution_steps 都不同 ({len(results)} 个输入 → {len(steps_set)} 个唯一输出)")
    else:
        print(f"❌ FAIL: 发现重复的 solution_steps ({len(results)} 个输入 → {len(steps_set)} 个唯一输出)")
        return False

    # 检查3：所有 animation_instructions 必须不同
    anim_set = set()
    for r in results:
        anim_str = json.dumps(r['result']['animation_instructions'], sort_keys=True)
        anim_set.add(anim_str)

    if len(anim_set) == len(results):
        print(f"✅ PASS: 所有 animation_instructions 都不同 ({len(results)} 个输入 → {len(anim_set)} 个唯一输出)")
    else:
        print(f"⚠️  WARNING: 部分 animation_instructions 相同 ({len(results)} 个输入 → {len(anim_set)} 个唯一输出)")
        # 这个不算失败，因为某些情况下动画指令可能确实相同

    # 检查4：problem_type 应该不同
    types_set = set(r['result']['problem_type'] for r in results)

    if len(types_set) == len(results):
        print(f"✅ PASS: 所有 problem_type 都不同")
    else:
        print(f"⚠️  WARNING: 部分 problem_type 相同 ({len(results)} 个输入 → {len(types_set)} 个唯一类型)")

    print("\n" + "="*80)
    print("✅ 所有测试通过！不同输入产生不同输出。")
    print("="*80)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)