/**
 * 前端快速测试脚本
 * 在浏览器控制台粘贴并运行此脚本，可快速测试所有功能
 */

window.PhysicsTestSuite = {
  // 测试数据集
  testData: {
    horizontal_projectile: {
      name: '平抛运动',
      text: '一个物体从8米高的平台以10m/s的速度水平抛出，重力加速度g=9.8m/s²，求物体的运动轨迹。',
      animation: {
        type: 'projectile',
        initial_speed: 10,
        angle: 0,
        gravity: 9.8,
        initial_x: 0,
        initial_y: 8,
        duration: 1.28,
        scale: 30
      }
    },
    free_fall: {
      name: '自由落体',
      text: '一个物体从12米高处自由下落，g=10m/s²，求下落时间和落地速度。',
      animation: {
        type: 'projectile',
        initial_speed: 0,
        angle: 90,
        gravity: 10,
        initial_x: 0,
        initial_y: 12,
        duration: 1.55,
        scale: 30
      }
    },
    projectile: {
      name: '斜抛运动',
      text: '将一个物体以15m/s的初速度、与水平面成45度角斜向上抛出，g=9.8m/s²，求物体的射程和最大高度。',
      animation: {
        type: 'projectile',
        initial_speed: 15,
        angle: 45,
        gravity: 9.8,
        initial_x: 0,
        initial_y: 0,
        duration: 2.16,
        scale: 20
      }
    }
  },

  // 当前动画引擎实例
  currentEngine: null,

  // 测试 1: 直接播放动画（无需后端）
  testAnimation(type = 'horizontal_projectile') {
    console.log(`\n🎬 测试动画: ${this.testData[type].name}`);

    const data = this.testData[type].animation;
    const canvas = document.getElementById('animationCanvas');

    if (!canvas) {
      console.error('❌ 找不到 Canvas 元素');
      return;
    }

    try {
      this.currentEngine = new AnimationEngine(canvas);
      this.currentEngine.loadInstructions(data);
      this.currentEngine.play();

      // 绑定控制按钮
      this.bindControls();

      console.log('✅ 动画加载成功');
      console.log('   类型:', data.type);
      console.log('   初速度:', data.initial_speed, 'm/s');
      console.log('   角度:', data.angle, '°');
      console.log('   持续时间:', data.duration, 's');
      console.log('\n💡 可用命令:');
      console.log('   PhysicsTestSuite.play()    - 播放');
      console.log('   PhysicsTestSuite.pause()   - 暂停');
      console.log('   PhysicsTestSuite.replay()  - 重播');
    } catch (error) {
      console.error('❌ 动画加载失败:', error);
    }
  },

  // 测试 2: 模拟完整上传流程
  async testUpload(type = 'horizontal_projectile') {
    console.log(`\n📤 测试上传: ${this.testData[type].name}`);

    const questionText = this.testData[type].text;
    const formData = new FormData();
    formData.append('manual_text', questionText);

    try {
      console.log('   发送请求...');
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ 后端响应成功');
      console.log('   题目类型:', data.problem_type);
      console.log('   运动类型:', data.parameters?.motion_type);

      // 渲染结果
      this.renderResults(data);

      // 播放动画
      const canvas = document.getElementById('animationCanvas');
      this.currentEngine = new AnimationEngine(canvas);
      this.currentEngine.loadInstructions(data.animation_instructions);
      this.currentEngine.play();
      this.bindControls();

      console.log('✅ 动画已开始播放');
      return data;
    } catch (error) {
      console.error('❌ 上传失败:', error);
      throw error;
    }
  },

  // 测试 3: 运行完整测试套件
  async runFullTest(delayBetweenTests = 3000) {
    console.log('\n🧪 开始完整测试套件...\n');
    console.log('═══════════════════════════════════════');

    const types = Object.keys(this.testData);
    const results = [];

    for (let i = 0; i < types.length; i++) {
      const type = types[i];
      console.log(`\n[${i + 1}/${types.length}] 测试: ${this.testData[type].name}`);
      console.log('───────────────────────────────────────');

      try {
        const result = await this.testUpload(type);
        results.push({ type, status: 'success', data: result });
        console.log(`✅ ${this.testData[type].name} - 通过`);

        if (i < types.length - 1) {
          console.log(`\n⏳ 等待 ${delayBetweenTests / 1000} 秒后继续...`);
          await new Promise(resolve => setTimeout(resolve, delayBetweenTests));
        }
      } catch (error) {
        results.push({ type, status: 'failed', error: error.message });
        console.error(`❌ ${this.testData[type].name} - 失败`);
      }
    }

    console.log('\n═══════════════════════════════════════');
    console.log('📊 测试报告');
    console.log('═══════════════════════════════════════');
    console.log(`总计: ${results.length}`);
    console.log(`通过: ${results.filter(r => r.status === 'success').length}`);
    console.log(`失败: ${results.filter(r => r.status === 'failed').length}`);
    console.log('═══════════════════════════════════════\n');

    return results;
  },

  // 渲染结果到页面
  renderResults(data) {
    // 渲染解题步骤
    const stepsContainer = document.getElementById('stepsContainer');
    if (stepsContainer) {
      stepsContainer.innerHTML = '<ol>' +
        (data.solution_steps || []).map(s => `<li>${s}</li>`).join('') +
        '</ol>';
    }

    // 渲染动画指令
    const instructionsContainer = document.getElementById('instructionsContainer');
    if (instructionsContainer) {
      instructionsContainer.innerHTML =
        `<pre>${JSON.stringify(data.animation_instructions, null, 2)}</pre>`;
    }

    // 渲染题目信息
    const metaContainer = document.getElementById('metaContainer');
    if (metaContainer) {
      metaContainer.innerHTML = `
        <ul>
          <li><strong>题目类型：</strong>${data.problem_type || '未知'}</li>
          <li><strong>运动类型：</strong>${data.parameters?.motion_type || '未知'}</li>
          <li><strong>OCR 预览：</strong>${(data.ocr_text || '').substring(0, 50)}...</li>
        </ul>
      `;
    }
  },

  // 绑定控制按钮
  bindControls() {
    const controls = document.getElementById('controls');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const replayBtn = document.getElementById('replayBtn');

    if (controls) controls.style.display = 'flex';

    if (playBtn) {
      playBtn.onclick = () => this.play();
    }
    if (pauseBtn) {
      pauseBtn.onclick = () => this.pause();
    }
    if (replayBtn) {
      replayBtn.onclick = () => this.replay();
    }
  },

  // 控制函数
  play() {
    if (this.currentEngine) {
      this.currentEngine.play();
      console.log('▶️  播放');
    }
  },

  pause() {
    if (this.currentEngine) {
      this.currentEngine.pause();
      console.log('⏸  暂停');
    }
  },

  replay() {
    if (this.currentEngine) {
      this.currentEngine.reset();
      this.currentEngine.play();
      console.log('🔄 重播');
    }
  },

  // 快速帮助
  help() {
    console.log('\n📖 前端测试命令帮助');
    console.log('═══════════════════════════════════════');
    console.log('PhysicsTestSuite.testAnimation(type)');
    console.log('  快速测试动画（无需后端）');
    console.log('  type: horizontal_projectile | free_fall | projectile');
    console.log('');
    console.log('PhysicsTestSuite.testUpload(type)');
    console.log('  测试完整上传流程（需要后端）');
    console.log('  type: horizontal_projectile | free_fall | projectile');
    console.log('');
    console.log('PhysicsTestSuite.runFullTest()');
    console.log('  运行完整测试套件（所有样例）');
    console.log('');
    console.log('PhysicsTestSuite.play()');
    console.log('  播放动画');
    console.log('');
    console.log('PhysicsTestSuite.pause()');
    console.log('  暂停动画');
    console.log('');
    console.log('PhysicsTestSuite.replay()');
    console.log('  重播动画');
    console.log('═══════════════════════════════════════\n');
  }
};

// 自动执行帮助
console.log('\n🎯 前端测试工具已加载！');
console.log('输入 PhysicsTestSuite.help() 查看帮助\n');
console.log('快速开始:');
console.log('  PhysicsTestSuite.testAnimation()      # 测试平抛动画');
console.log('  PhysicsTestSuite.testUpload()         # 测试完整流程');
console.log('  PhysicsTestSuite.runFullTest()        # 运行所有测试\n');