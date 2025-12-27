/**
 * 动画模块合并自动化测试脚本
 *
 * 使用方法：
 * 1. 打开浏览器访问 http://127.0.0.1:5001/test
 * 2. 打开控制台（F12）
 * 3. 复制此脚本并粘贴到控制台执行
 */

(async function runAutomatedTests() {
  console.log('\n'.repeat(3));
  console.log('='.repeat(80));
  console.log('🧪 Canvas 动画模块合并自动化测试');
  console.log('='.repeat(80));
  console.log('\n');

  const results = {
    passed: 0,
    failed: 0,
    total: 0
  };

  // 测试辅助函数
  function assert(condition, message) {
    results.total++;
    if (condition) {
      results.passed++;
      console.log(`✅ PASS: ${message}`);
      return true;
    } else {
      results.failed++;
      console.error(`❌ FAIL: ${message}`);
      return false;
    }
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  console.log('📋 阶段 1：检查全局对象加载\n');

  assert(
    typeof AnimationEngine !== 'undefined',
    'AnimationEngine 类已加载（兼容适配层）'
  );

  assert(
    typeof PhysicsVisualizer !== 'undefined',
    'PhysicsVisualizer 类已加载（核心引擎）'
  );

  assert(
    typeof AnimationBase !== 'undefined',
    'AnimationBase 类已加载（基类）'
  );

  assert(
    typeof FreeFall !== 'undefined',
    'FreeFall 类已加载（自由落体实现）'
  );

  assert(
    typeof ProjectileMotion !== 'undefined',
    'ProjectileMotion 类已加载（抛体运动实现）'
  );

  console.log('\n');
  console.log('📋 阶段 2：测试数据格式转换\n');

  // 测试旧格式转换
  const oldFormatData = {
    type: 'projectile',
    initial_speed: 15,
    angle: 30,
    gravity: 9.8
  };

  const normalized = AnimationEngine.normalizePayload(oldFormatData);

  assert(
    normalized !== null,
    '旧格式数据能成功标准化'
  );

  assert(
    normalized.sub_type === 'projectile_motion',
    '旧格式 type="projectile" 转换为 sub_type="projectile_motion"'
  );

  assert(
    normalized.parameters.v0 === 15,
    '旧格式 initial_speed 转换为 parameters.v0'
  );

  assert(
    normalized.parameters.angle === 30,
    '旧格式 angle 保持不变'
  );

  // 测试新格式直通
  const newFormatData = {
    sub_type: 'free_fall',
    parameters: {
      height: 20,
      g: 9.8,
      mass: 1
    }
  };

  const passthrough = AnimationEngine.normalizePayload(newFormatData);

  assert(
    passthrough.sub_type === 'free_fall',
    '新格式数据直接通过，不做转换'
  );

  console.log('\n');
  console.log('📋 阶段 3：测试 Canvas 初始化\n');

  // 创建临时 Canvas
  const testCanvas = document.createElement('canvas');
  testCanvas.id = 'test-canvas-temp';
  testCanvas.width = 600;
  testCanvas.height = 400;
  document.body.appendChild(testCanvas);

  let engine;
  try {
    engine = new AnimationEngine(testCanvas);
    assert(
      engine !== null,
      'AnimationEngine 构造函数成功执行'
    );

    assert(
      engine.canvas === testCanvas,
      'Canvas 元素正确绑定'
    );

    assert(
      engine.visualizer instanceof PhysicsVisualizer,
      '内部 PhysicsVisualizer 实例化成功'
    );
  } catch (error) {
    assert(false, `AnimationEngine 初始化失败: ${error.message}`);
  }

  console.log('\n');
  console.log('📋 阶段 4：测试动画加载与播放\n');

  try {
    // 测试加载旧格式数据
    engine.loadInstructions({
      type: 'projectile',
      initial_speed: 20,
      angle: 45,
      gravity: 9.8
    });

    assert(
      engine.visualizer.currentAnimation !== null,
      '旧格式数据加载后创建了动画实例'
    );

    assert(
      engine.visualizer.currentAnimation instanceof ProjectileMotion,
      '正确创建了 ProjectileMotion 实例'
    );

    // 测试播放控制
    engine.play();
    assert(
      engine.isPlaying === true,
      'play() 方法正确设置播放状态'
    );

    await sleep(500);

    engine.pause();
    assert(
      engine.isPlaying === false,
      'pause() 方法正确设置暂停状态'
    );

    engine.reset();
    assert(
      true,
      'reset() 方法执行无错误'
    );

  } catch (error) {
    assert(false, `动画加载/播放测试失败: ${error.message}`);
  }

  console.log('\n');
  console.log('📋 阶段 5：测试自由落体动画\n');

  try {
    engine.loadInstructions({
      sub_type: 'free_fall',
      parameters: {
        height: 15,
        g: 9.8,
        mass: 1
      }
    });

    assert(
      engine.visualizer.currentAnimation instanceof FreeFall,
      '新格式自由落体数据正确创建 FreeFall 实例'
    );

    engine.play();
    await sleep(500);
    engine.pause();

    assert(
      true,
      '自由落体动画播放无错误'
    );

  } catch (error) {
    assert(false, `自由落体测试失败: ${error.message}`);
  }

  // 清理
  document.body.removeChild(testCanvas);

  console.log('\n');
  console.log('='.repeat(80));
  console.log('📊 测试结果汇总');
  console.log('='.repeat(80));
  console.log(`总测试数: ${results.total}`);
  console.log(`通过: ${results.passed} ✅`);
  console.log(`失败: ${results.failed} ❌`);
  console.log(`成功率: ${((results.passed / results.total) * 100).toFixed(2)}%`);
  console.log('='.repeat(80));

  if (results.failed === 0) {
    console.log('\n🎉 恭喜！所有测试通过，动画模块合并成功！\n');
  } else {
    console.error('\n⚠️ 部分测试失败，请检查上面的错误信息。\n');
  }

  return {
    success: results.failed === 0,
    results
  };
})();