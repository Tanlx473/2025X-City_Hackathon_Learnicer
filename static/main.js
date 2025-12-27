const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const loadingEl = document.getElementById('loading');
const stepsContainer = document.getElementById('stepsContainer');
const instructionsContainer = document.getElementById('instructionsContainer');
const metaContainer = document.getElementById('metaContainer');
const canvas = document.getElementById('animationCanvas');
const controls = document.getElementById('controls');
const playBtn = document.getElementById('playBtn');
const pauseBtn = document.getElementById('pauseBtn');
const replayBtn = document.getElementById('replayBtn');
const errorBox = document.getElementById('errorBox');

let engine = null;
const submitButton = uploadForm.querySelector('button[type="submit"]');

controls.style.display = 'none';

function setLoading(isLoading) {
  loadingEl.style.display = isLoading ? 'flex' : 'none';
  submitButton.disabled = isLoading;
}

function showError(message) {
  if (!message) {
    errorBox.style.display = 'none';
    errorBox.textContent = '';
    return;
  }
  errorBox.textContent = message;
  errorBox.style.display = 'block';
}

function renderSteps(steps) {
  stepsContainer.innerHTML = '';
  if (!steps || !Array.isArray(steps) || steps.length === 0) {
    stepsContainer.textContent = '未获取到解题步骤。';
    return;
  }
  const ol = document.createElement('ol');
  steps.forEach((step) => {
    const li = document.createElement('li');
    li.textContent = typeof step === 'string' ? step : JSON.stringify(step);
    ol.appendChild(li);
  });
  stepsContainer.appendChild(ol);
}

function renderInstructions(rawInstructions) {
  instructionsContainer.innerHTML = '';
  if (!rawInstructions) {
    instructionsContainer.textContent = '暂无动画指令';
    return;
  }

  if (Array.isArray(rawInstructions)) {
    const ul = document.createElement('ul');
    rawInstructions.forEach((item) => {
      const li = document.createElement('li');
      li.textContent = typeof item === 'string' ? item : JSON.stringify(item, null, 2);
      ul.appendChild(li);
    });
    instructionsContainer.appendChild(ul);
  } else if (typeof rawInstructions === 'object') {
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(rawInstructions, null, 2);
    instructionsContainer.appendChild(pre);
  } else {
    instructionsContainer.textContent = String(rawInstructions);
  }
}

function renderMeta(data) {
  metaContainer.innerHTML = '';
  const list = document.createElement('ul');

  const items = [
    ['题目类型', data.problem_type || '未知'],
    ['OCR 预览', data.ocr_text ? `${data.ocr_text.slice(0, 80)}${data.ocr_text.length > 80 ? '…' : ''}` : '无'],
  ];

  if (data.parameters && typeof data.parameters === 'object') {
    items.push(['参数', JSON.stringify(data.parameters, null, 2)]);
  }

  items.forEach(([label, value]) => {
    const li = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = `${label}：`;
    li.appendChild(strong);
    li.appendChild(document.createTextNode(value));
    list.appendChild(li);
  });
  metaContainer.appendChild(list);
}

function normalizeAnimationData(raw) {
  if (!raw) return null;

  if (Array.isArray(raw)) {
    // 占位数组场景：使用一个默认的抛体运动示例，确保画布可演示
    return {
      type: 'projectile',
      initial_speed: 18,
      angle: 55,
      gravity: 9.8,
      initial_x: 0,
      initial_y: 0,
      scale: 24,
      duration: 4,
    };
  }

  if (typeof raw === 'object') {
    // 如果是对象，直接返回用于动画解析
    return raw;
  }

  return null;
}

function bindControls(currentEngine) {
  controls.style.display = 'flex';
  playBtn.onclick = () => currentEngine.play();
  pauseBtn.onclick = () => currentEngine.pause();
  replayBtn.onclick = () => {
    currentEngine.reset();
    currentEngine.play();
  };
}

function resetCanvas() {
  if (engine) {
    engine.pause();
  }
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  controls.style.display = 'none';
}

uploadForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) {
    showError('请选择一张图片再上传');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  showError('');
  setLoading(true);
  resetCanvas();
  stepsContainer.textContent = '';
  instructionsContainer.textContent = '';
  metaContainer.textContent = '';

  fetch('/upload', {
    method: 'POST',
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`上传失败，状态码：${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      setLoading(false);
      renderSteps(data.solution_steps || data.steps);
      renderInstructions(data.animation_instructions);
      renderMeta(data);

      const animationData = normalizeAnimationData(data.animation_instructions);
      if (!animationData) {
        showError('后端未返回可用的动画数据，已跳过动画演示。');
        return;
      }

      try {
        engine = new AnimationEngine(canvas);
        engine.loadInstructions(animationData);
        bindControls(engine);
        engine.play();
      } catch (err) {
        console.error('动画初始化失败:', err);
        showError(`动画初始化失败: ${err.message}`);
      }
    })
    .catch((error) => {
      console.error(error);
      setLoading(false);
      showError(`很抱歉，解析失败，请重试。错误信息: ${error.message}`);
    });
});
