#!/usr/bin/env python3
"""
前端集成测试：验证后端返回的数据能被前端正确处理

测试流程：
1. 上传不同的文本（模拟不同图片）
2. 验证后端返回不同的响应
3. 模拟前端 AnimationEngine.normalizePayload 处理
4. 确认最终传给动画引擎的参数不同
"""

import sys
import requests
import json

BASE_URL = "http://127.0.0.1:5000"


def simulate_frontend_normalize(backend_response):
    """
    模拟前端 AnimationEngine.normalizePayload 的处理逻辑
    """
    raw = backend_response.get('animation_instructions', {})

    if not raw:
        return None

    # 检查是否已是新格式
    if 'sub_type' in raw and 'parameters' in raw:
        return raw

    # 旧格式转新格式
    motion_type = raw.get('motion_type_original') or raw.get('type') or 'projectile'

    # 映射类型
    if motion_type == 'free_fall':
        sub_type = 'free_fall'
    elif motion_type == 'uniform':
        sub_type = 'uniform'
    else:
        sub_type = 'projectile_motion'

    # 提取参数（使用修复后的逻辑）
    parameters = {
        'v0': raw.get('initial_speed') if 'initial_speed' in raw else (raw.get('v0') if 'v0' in raw else 20),
        'angle': raw.get('angle') if 'angle' in raw else 45,
        'g': raw.get('gravity') if 'gravity' in raw else (raw.get('g') if 'g' in raw else 9.8),
        'h0': raw.get('initial_y') if 'initial_y' in raw else (raw.get('h0') if 'h0' in raw else 0),
        'mass': raw.get('mass') if 'mass' in raw else 1,
        'scale': raw.get('scale'),
        'duration': raw.get('duration')
    }

    return {
        'sub_type': sub_type,
        'parameters': parameters
    }


def test_integration(text, description):
    """测试一个场景"""
    print(f"\n{'='*80}")
    print(f"测试: {description}")
    print(f"{'='*80}")
    print(f"输入文本: {text}")

    # 1. 发送请求
    response = requests.post(f"{BASE_URL}/upload", data={"manual_text": text})

    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        return None

    backend_data = response.json()

    # 2. 显示后端返回
    print(f"\n后端返回的 animation_instructions:")
    anim = backend_data.get('animation_instructions', {})
    print(f"  type: {anim.get('type')}")
    print(f"  motion_type_original: {anim.get('motion_type_original')}")
    print(f"  initial_speed: {anim.get('initial_speed')}")
    print(f"  angle: {anim.get('angle')}")
    print(f"  initial_y: {anim.get('initial_y')}")

    # 3. 模拟前端处理
    normalized = simulate_frontend_normalize(backend_data)
    print(f"\n前端 normalizePayload 后:")
    print(f"  sub_type: {normalized.get('sub_type')}")
    print(f"  v0: {normalized['parameters'].get('v0')}")
    print(f"  angle: {normalized['parameters'].get('angle')}")
    print(f"  h0: {normalized['parameters'].get('h0')}")

    return {
        'description': description,
        'backend': backend_data,
        'normalized': normalized
    }


def main():
    """主测试函数"""

    # 检查服务是否运行
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        if health.status_code != 200:
            print("❌ 服务未运行。请先启动: python app.py")
            return False
    except:
        print("❌ 无法连接到服务。请先启动: python app.py")
        return False

    print("\n" + "="*80)
    print("前端集成测试：验证完整数据流")
    print("="*80)

    # 测试用例
    test_cases = [
        ("一小球以 15 m/s 的初速度水平抛出，从 10 米高的平台", "平抛运动"),
        ("一物体从 20 米高处自由落体", "自由落体"),
        ("以 25 m/s 的初速度以 60° 角斜向上抛出", "斜抛运动"),
    ]

    results = []

    for text, description in test_cases:
        result = test_integration(text, description)
        if result is None:
            print(f"\n❌ 测试失败：{description}")
            return False
        results.append(result)

    # 验证结果
    print("\n" + "="*80)
    print("验证结果")
    print("="*80)

    # 检查：所有角度应该不同
    angles = [r['normalized']['parameters']['angle'] for r in results]
    print(f"\n角度值: {angles}")

    if len(set(angles)) == len(angles):
        print(f"✅ PASS: 所有角度都不同 ({angles})")
    else:
        print(f"❌ FAIL: 发现重复的角度 ({angles})")
        return False

    # 检查：所有速度应该不同
    speeds = [r['normalized']['parameters']['v0'] for r in results]
    print(f"速度值: {speeds}")

    if len(set(speeds)) == len(speeds):
        print(f"✅ PASS: 所有速度都不同 ({speeds})")
    else:
        print(f"❌ FAIL: 发现重复的速度 ({speeds})")
        return False

    # 检查：所有高度应该不同
    heights = [r['normalized']['parameters']['h0'] for r in results]
    print(f"高度值: {heights}")

    if len(set(heights)) == len(heights):
        print(f"✅ PASS: 所有高度都不同 ({heights})")
    else:
        print(f"❌ FAIL: 发现重复的高度 ({heights})")
        return False

    print("\n" + "="*80)
    print("✅ 所有测试通过！")
    print("前端能够正确处理后端返回的不同数据。")
    print("="*80)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)