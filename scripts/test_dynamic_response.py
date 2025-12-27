#!/usr/bin/env python3
"""
测试脚本：验证不同输入产生不同输出

测试场景：
1. 不同的 OCR 文本应产生不同的 solution_steps 和 animation_instructions
2. 验证运动类型分类功能
3. 验证参数提取功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置环境变量（避免真实调用 LLM，使用规则引擎测试）
os.environ['ENABLE_LLM'] = 'false'
os.environ['CLAUDE_API_KEY'] = ''

from flask import Flask
from services.llm_service import analyze_physics_text

def test_different_inputs():
    """测试不同输入产生不同输出"""

    # 创建临时 Flask app（用于 current_app.config）
    app = Flask(__name__)
    app.config['ENABLE_LLM'] = False
    app.config['CLAUDE_API_KEY'] = ''

    with app.app_context():
        # 测试用例1：平抛运动
        text1 = "一小球以 15 m/s 的初速度水平抛出，从 10 米高的平台，g = 9.8 m/s²"

        # 测试用例2：自由落体
        text2 = "一物体从 20 米高处自由落体，重力加速度 g = 9.8 m/s²"

        # 测试用例3：斜抛运动
        text3 = "以 25 m/s 的初速度以 60° 角斜向上抛出，g = 9.8 m/s²"

        # 测试用例4：匀速直线
        text4 = "一辆车以 5 m/s 的速度匀速直线运动"

        test_cases = [
            ("平抛运动", text1),
            ("自由落体", text2),
            ("斜抛运动", text3),
            ("匀速直线", text4),
        ]

        results = []

        print("\n" + "=" * 80)
        print("测试：不同输入产生不同输出")
        print("=" * 80)

        for name, ocr_text in test_cases:
            print(f"\n【测试 {len(results) + 1}】{name}")
            print(f"输入文本: {ocr_text[:50]}...")

            result = analyze_physics_text(ocr_text)

            print(f"问题类型: {result['problem_type']}")
            print(f"解题步骤数: {len(result['solution_steps'])}")
            print(f"解题步骤: {result['solution_steps']}")
            print(f"动画类型: {result['animation_instructions'].get('type')}")
            print(f"动画参数: speed={result['animation_instructions'].get('initial_speed')}, " +
                  f"angle={result['animation_instructions'].get('angle')}")

            results.append({
                'name': name,
                'ocr_text': ocr_text,
                'result': result
            })

        # 验证结果
        print("\n" + "=" * 80)
        print("验证结果")
        print("=" * 80)

        # 检查1：所有结果的 solution_steps 应该不同
        steps_set = set()
        for r in results:
            steps_str = str(r['result']['solution_steps'])
            steps_set.add(steps_str)

        if len(steps_set) == len(results):
            print("✅ PASS: 所有测试用例的 solution_steps 都不同")
        else:
            print(f"❌ FAIL: 发现重复的 solution_steps（{len(results)} 个输入，{len(steps_set)} 个唯一输出）")
            return False

        # 检查2：运动类型应该正确分类
        expected_types = {
            "平抛运动": "horizontal_projectile",
            "自由落体": "free_fall",
            "斜抛运动": "projectile",
            "匀速直线": "uniform",
        }

        all_correct = True
        for r in results:
            expected = expected_types[r['name']]
            actual = r['result']['animation_instructions'].get('motion_type_original')

            if actual == expected:
                print(f"✅ {r['name']}: 类型正确 ({actual})")
            else:
                print(f"❌ {r['name']}: 类型错误 (expected={expected}, actual={actual})")
                all_correct = False

        if all_correct:
            print("\n✅ 所有测试通过！不同输入确实产生不同输出。")
            return True
        else:
            print("\n❌ 部分测试失败！")
            return False


if __name__ == '__main__':
    success = test_different_inputs()
    sys.exit(0 if success else 1)