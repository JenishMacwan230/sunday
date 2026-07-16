/* ═══════════════════════════════════════════════════════════════
   SUNDAY AI Voice Assistant — Application Logic (Compact Theme)
   ═══════════════════════════════════════════════════════════════ */

// ── State ─────────────────────────────────────────────────────
const state = {
  expanded: true,
  status: 'idle',           // idle | listening | thinking | speaking | wakeword | cooldown
  isListening: false,
  isMuted: false,
  isPaused: false,
  mode: 'manual',           // 'manual' | 'wakeword'
};

let activeListenRequestId = 0;

// ── Current Task Tracking ─────────────────────────────────────
let currentTask = null;  // { name, status, startTime }

// ── DOM References ────────────────────────────────────────────
const widget        = document.getElementById('widget');
const expandedPanel = document.getElementById('expandedPanel');
const statusBadge   = document.getElementById('statusBadge');
const statusText    = document.getElementById('statusText');
const statusDotLive = document.getElementById('statusDotLive');
const headerSubtitle = document.getElementById('headerSubtitle');
const actionOrb     = document.getElementById('actionOrb');
const micIcon       = document.getElementById('micIcon');
const stopIcon      = document.getElementById('stopIcon');
const spokenCommandText = document.getElementById('spokenCommandText');
const canvas        = document.getElementById('visualizerCanvas');
const ctx           = canvas.getContext('2d');
const currentTaskArea = document.getElementById('currentTaskArea');
const responseBox   = document.getElementById('responseBox');
const responseTextEl = document.getElementById('responseText');

// ── Toggle Expand / Collapse (no-op for window app) ──────────
// Kept as stub in case any residual calls exist
function toggleExpand() {}
function goBack() {}

// ── Status Management ─────────────────────────────────────────
function setStatus(newStatus) {
  state.status = newStatus;

  const labels = { idle: 'Idle', listening: 'Listening…', thinking: 'Thinking…', speaking: 'Speaking…', wakeword: 'Listening…', cooldown: 'Cooldown…' };
  const subtitles = {
    idle: 'AI Voice Assistant',
    listening: 'Listening for your command…',
    thinking: 'Processing your request…',
    speaking: 'Responding…',
    wakeword: 'Say "Hey Sunday" to activate…',
    cooldown: 'Resetting — please wait…',
  };

  statusText.textContent = labels[newStatus];
  headerSubtitle.textContent = subtitles[newStatus];

  statusDotLive.className = 'status-dot-live';
  if (newStatus !== 'idle') statusDotLive.classList.add(newStatus);
}

// ── Current Task Display ──────────────────────────────────────
function setCurrentTask(name, status) {
  currentTask = { name, status, startTime: Date.now() };
  renderCurrentTask();
}

function clearCurrentTask() {
  currentTask = null;
  renderCurrentTask();
}

function renderCurrentTask() {
  if (!currentTaskArea) return;

  if (!currentTask) {
    currentTaskArea.innerHTML = `
      <div class="current-task-empty">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.35">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 12h8"/>
        </svg>
        <p>No active task</p>
      </div>`;
    return;
  }

  const statusClass = currentTask.status || 'running';
  const statusIcon = statusClass === 'running'
    ? '<span class="status-spinner"></span>'
    : statusClass === 'completed' ? '✓' : statusClass === 'failed' ? '✕' : '';

  currentTaskArea.innerHTML = `
    <div class="task-item active-glow">
      <div class="task-icon yellow">
        <span>${statusClass === 'running' ? '⚡' : statusClass === 'completed' ? '✅' : '❌'}</span>
      </div>
      <div class="task-info">
        <div class="task-name">${currentTask.name}</div>
        <div class="task-meta">
          <span class="task-status ${statusClass}">
            ${statusIcon}
            ${capitalize(statusClass)}
          </span>
          <span>${getElapsedTime(currentTask.startTime)}</span>
        </div>
        ${statusClass === 'running' ? '<div class="task-progress"><div class="task-progress-bar thinking-bar"></div></div>' : ''}
      </div>
    </div>`;
}

function getElapsedTime(startTime) {
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  if (elapsed < 60) return `${elapsed}s ago`;
  return `${Math.floor(elapsed / 60)}m ago`;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Cooldown Countdown ────────────────────────────────────────
const COOLDOWN_SECONDS = 1;  // Matches backend COOLDOWN_SECONDS

/**
 * Replaces the mic button content with a countdown timer for the
 * cooldown period, then restores the mic icon when done.
 */
function showCooldownCountdown(seconds) {
  return new Promise(resolve => {
    setStatus('cooldown');

    const orb = document.getElementById('actionOrb');
    const mic = document.getElementById('micIcon');
    const stop = document.getElementById('stopIcon');
    const cooldownTimer = document.getElementById('cooldownTimer');
    const countdownNum = document.getElementById('countdownNumber');
    const countdownRing = document.getElementById('countdownRing');

    if (!cooldownTimer || !countdownNum) {
      setTimeout(resolve, seconds * 1000);
      return;
    }

    // Hide mic & stop icons, show timer
    mic.classList.add('hidden');
    stop.classList.add('hidden');
    cooldownTimer.classList.remove('hidden');
    orb.classList.add('cooldown');
    orb.classList.remove('listening');

    // Disable clicking during cooldown
    orb.style.pointerEvents = 'none';

    let remaining = seconds;
    countdownNum.textContent = remaining;

    // Animate the ring
    if (countdownRing) {
      const circumference = 2 * Math.PI * 28; // radius=28
      countdownRing.style.strokeDasharray = circumference;
      countdownRing.style.strokeDashoffset = '0';
      countdownRing.style.transition = 'none';
      void countdownRing.offsetWidth; // force reflow
      countdownRing.style.transition = `stroke-dashoffset ${seconds}s linear`;
      countdownRing.style.strokeDashoffset = circumference;
    }

    updateSpokenCommand('⏳ Cooling down...');
    updateResponse(`Resetting in ${remaining}s...`);

    const interval = setInterval(() => {
      remaining--;
      if (remaining > 0) {
        countdownNum.textContent = remaining;
        updateResponse(`Resetting in ${remaining}s...`);
      } else {
        clearInterval(interval);
        countdownNum.textContent = '✓';
        updateResponse('Ready for next command!');

        // Brief flash of "✓" then restore mic
        setTimeout(() => {
          cooldownTimer.classList.add('hidden');
          mic.classList.remove('hidden');
          orb.classList.remove('cooldown');
          orb.style.pointerEvents = '';
          setStatus('idle');
          resolve();
        }, 400);
      }
    }, 1000);
  });
}

// ── Listening Toggle ──────────────────────────────────────────
function toggleListening() {
  // Block listening when muted
  if (state.isMuted && !state.isListening) {
    updateSpokenCommand('Mic is muted. Unmute to use.');
    updateResponse('Tap "Unmute" to start listening again.');
    return;
  }

  // Block listening when paused
  if (state.isPaused && !state.isListening) {
    updateSpokenCommand('Assistant is paused. Resume to use.');
    updateResponse('Tap "Resume" to start listening again.');
    return;
  }

  state.isListening = !state.isListening;

  if (state.isListening) {
    setListeningVisualState(true);
    if (state.mode === 'wakeword') {
      updateSpokenCommand('Listening for "Hey Sunday"...');
      updateResponse('Say "Hey Sunday" to activate...');
      wakeWordContinuousLoop();
    } else {
      updateSpokenCommand('Listening...');
      listenAndDisplayCommand();
    }
  } else {
    activeListenRequestId++;
    setListeningVisualState(false);
    updateSpokenCommand('Tap the mic and say your command...');
    updateResponse('Waiting for your command...');
    setStatus('idle');
  }
}

function setListeningVisualState(isListening) {
  if (isListening) {
    setStatus('listening');
    actionOrb.classList.add('listening');
    micIcon.classList.add('hidden');
    stopIcon.classList.remove('hidden');
    return;
  }

  state.isListening = false;
  setStatus('idle');
  actionOrb.classList.remove('listening');
  micIcon.classList.remove('hidden');
  stopIcon.classList.add('hidden');
}

function updateSpokenCommand(text) {
  if (!spokenCommandText) return;
  spokenCommandText.textContent = text;
}

function updateResponse(text) {
  if (!responseTextEl || !responseBox) return;
  responseTextEl.textContent = text;
  if (text && text !== 'Waiting for your command...') {
    responseBox.classList.add('has-response');
  } else {
    responseBox.classList.remove('has-response');
  }
}

async function listenAndDisplayCommand() {
  const requestId = ++activeListenRequestId;

  if (typeof eel === 'undefined' || typeof eel.allCommands !== 'function') {
    updateSpokenCommand('Voice service is not connected.');
    updateResponse('Cannot connect to voice backend.');
    setListeningVisualState(false);
    return;
  }

  try {
    setCurrentTask('Processing voice command…', 'running');
    updateResponse('Processing...');
    setStatus('thinking');
    const query = await eel.allCommands()();
    if (requestId !== activeListenRequestId) return;

    // Handle paused state from backend
    if (query === '__PAUSED__') {
      updateSpokenCommand('Assistant is paused.');
      updateResponse('Resume the assistant to process commands.');
      setCurrentTask('Paused', 'failed');
      setTimeout(clearCurrentTask, 3000);
      setListeningVisualState(false);
      return;
    }

    if (query && query.trim()) {
      updateSpokenCommand(query.trim());
      // Build response based on command
      if (query.includes('send message') || query.includes('whatsapp') || query.includes('send whatsapp')) {
        updateResponse('Sending WhatsApp message...');
        setCurrentTask('Sending WhatsApp message', 'completed');
      } else if (query.includes('open')) {
        const appName = query.replace('sunday', '').replace('open', '').trim();
        updateResponse(`Opening ${appName}...`);
        setCurrentTask(`Opening ${appName}`, 'completed');
      } else if (query.includes('on youtube')) {
        updateResponse('Playing on YouTube...');
        setCurrentTask('Playing on YouTube', 'completed');
      } else {
        updateResponse('Command not recognized. Please try again.');
        setCurrentTask('Unrecognized command', 'failed');
      }
      // Auto-clear completed/failed task after cooldown
      setTimeout(clearCurrentTask, 5000);
    } else {
      updateSpokenCommand("I couldn't catch that. Try again.");
      updateResponse('No command detected.');
      clearCurrentTask();
    }

    // ── 3-second cooldown countdown (backend is also sleeping) ──
    if (query && query.trim() && query !== '__PAUSED__') {
      await showCooldownCountdown(COOLDOWN_SECONDS);
    }
  } catch (error) {
    console.error('Voice command failed:', error);
    if (requestId !== activeListenRequestId) return;
    updateSpokenCommand('Error while listening. Please try again.');
    updateResponse('An error occurred.');
    setCurrentTask('Error occurred', 'failed');
    setTimeout(clearCurrentTask, 4000);
  } finally {
    if (requestId === activeListenRequestId) {
      setListeningVisualState(false);
    }
  }
}

// ── Mute Toggle (calls backend) ──────────────────────────────
async function toggleMute() {
  state.isMuted = !state.isMuted;
  const btn = document.getElementById('btnMute');
  const iconOn = document.getElementById('iconVolumeOn');
  const iconOff = document.getElementById('iconVolumeOff');

  if (state.isMuted) {
    btn.classList.add('muted');
    btn.querySelector('span').textContent = 'Unmute';
    iconOn.classList.add('hidden');
    iconOff.classList.remove('hidden');

    // Freeze the mic button — stop any active listening
    if (state.isListening) {
      activeListenRequestId++;
      setListeningVisualState(false);
      updateSpokenCommand('Mic muted.');
    }
    actionOrb.classList.add('disabled');
    headerSubtitle.textContent = 'Muted — tap Unmute to use mic';
  } else {
    btn.classList.remove('muted');
    btn.querySelector('span').textContent = 'Mute';
    iconOn.classList.remove('hidden');
    iconOff.classList.add('hidden');

    // Unfreeze the mic button
    if (!state.isPaused) {
      actionOrb.classList.remove('disabled');
    }
    setStatus('idle');
  }

  // Call backend to actually mute/unmute TTS
  if (typeof eel !== 'undefined' && typeof eel.set_mute === 'function') {
    try {
      await eel.set_mute(state.isMuted)();
    } catch (e) {
      console.error('Failed to set mute state:', e);
    }
  }
}

// ── Pause Toggle (calls backend + stops listening) ───────────
async function togglePause() {
  state.isPaused = !state.isPaused;
  const btn = document.getElementById('btnPause');
  const iconPause = document.getElementById('iconPause');
  const iconPlay = document.getElementById('iconPlay');

  if (state.isPaused) {
    btn.classList.add('paused');
    btn.querySelector('span').textContent = 'Resume';
    iconPause.classList.add('hidden');
    iconPlay.classList.remove('hidden');

    // Force stop listening if currently active
    if (state.isListening) {
      activeListenRequestId++;
      setListeningVisualState(false);
      updateSpokenCommand('Assistant paused.');
    }
    setStatus('idle');
    headerSubtitle.textContent = 'Paused — tap Resume to continue';

    // Disable the mic orb visually
    actionOrb.classList.add('disabled');
  } else {
    btn.classList.remove('paused');
    btn.querySelector('span').textContent = 'Pause';
    iconPause.classList.remove('hidden');
    iconPlay.classList.add('hidden');
    setStatus('idle');

    // Re-enable the mic orb
    actionOrb.classList.remove('disabled');
  }

  // Call backend to set paused state
  if (typeof eel !== 'undefined' && typeof eel.set_paused === 'function') {
    try {
      await eel.set_paused(state.isPaused)();
    } catch (e) {
      console.error('Failed to set pause state:', e);
    }
  }
}

// ═══════════════════════════════════════════════════════════════
//  VOICE VISUALIZER (Canvas — Warm Sun Palette, optimized)
// ═══════════════════════════════════════════════════════════════
let animFrame;
const barCount = 48;
const barData  = new Float32Array(barCount).fill(0);
const barTarget = new Float32Array(barCount).fill(0);
let lastFrameTime = 0;
const TARGET_FPS = 60;
const FRAME_INTERVAL = 1000 / TARGET_FPS;

function drawVisualizer(timestamp) {
  // Frame throttle for consistent performance
  if (timestamp - lastFrameTime < FRAME_INTERVAL) {
    animFrame = requestAnimationFrame(drawVisualizer);
    return;
  }
  lastFrameTime = timestamp;

  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth * dpr;
  const H = canvas.clientHeight * dpr;

  if (canvas.width !== W || canvas.height !== H) {
    canvas.width = W;
    canvas.height = H;
  }

  ctx.clearRect(0, 0, W, H);

  const isActive = state.status === 'listening' || state.status === 'speaking';
  const isThinking = state.status === 'thinking';
  const isCooldown = state.status === 'cooldown';

  for (let i = 0; i < barCount; i++) {
    if (isActive) {
      barTarget[i] = 0.15 + Math.random() * 0.85;
    } else if (isThinking) {
      barTarget[i] = 0.1 + Math.sin(timestamp / 300 + i * 0.3) * 0.3 + 0.3;
    } else if (isCooldown) {
      // Gentle pulsing wave during cooldown
      barTarget[i] = 0.05 + Math.sin(timestamp / 500 + i * 0.4) * 0.15 + 0.15;
    } else {
      barTarget[i] = 0.02 + Math.sin(timestamp / 1000 + i * 0.2) * 0.03;
    }
    barData[i] += (barTarget[i] - barData[i]) * (isActive ? 0.25 : 0.08);
  }

  const gap = 2 * dpr;
  const barW = (W - gap * (barCount - 1)) / barCount;
  const maxH = H * 0.8;
  const centerY = H / 2;

  for (let i = 0; i < barCount; i++) {
    const x = i * (barW + gap);
    const h = barData[i] * maxH;

    const gradient = ctx.createLinearGradient(x, centerY - h / 2, x, centerY + h / 2);

    if (isActive) {
      gradient.addColorStop(0, 'rgba(255, 213, 79, 0.95)');
      gradient.addColorStop(0.5, 'rgba(255, 152, 0, 0.8)');
      gradient.addColorStop(1, 'rgba(255, 183, 77, 0.9)');
    } else if (isThinking) {
      gradient.addColorStop(0, 'rgba(255, 152, 0, 0.6)');
      gradient.addColorStop(1, 'rgba(255, 213, 79, 0.3)');
    } else if (isCooldown) {
      gradient.addColorStop(0, 'rgba(206, 147, 216, 0.5)');
      gradient.addColorStop(1, 'rgba(255, 183, 77, 0.25)');
    } else {
      gradient.addColorStop(0, 'rgba(255, 213, 79, 0.12)');
      gradient.addColorStop(1, 'rgba(255, 152, 0, 0.06)');
    }

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.roundRect(x, centerY - h / 2, barW, h, 1.5 * dpr);
    ctx.fill();
  }

  if (isActive || isThinking || isCooldown) {
    ctx.strokeStyle = isActive
      ? 'rgba(255, 183, 77, 0.1)'
      : isCooldown ? 'rgba(206, 147, 216, 0.08)'
      : 'rgba(255, 152, 0, 0.06)';
    ctx.lineWidth = 1 * dpr;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(W, centerY);
    ctx.stroke();
  }

  animFrame = requestAnimationFrame(drawVisualizer);
}

// ═══════════════════════════════════════════════════════════════
//  Pause visualizer when tab is not visible
// ═══════════════════════════════════════════════════════════════
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    if (animFrame) cancelAnimationFrame(animFrame);
  } else {
    lastFrameTime = 0;
    animFrame = requestAnimationFrame(drawVisualizer);
  }
});

// ═══════════════════════════════════════════════════════════════
//  APP PATHS MODAL
// ═══════════════════════════════════════════════════════════════

function openAppPaths() {
  const modal = document.getElementById('appPathsModal');
  if (modal) {
    modal.classList.remove('hidden');
    loadAppPaths();
  }
}

function closeAppPaths() {
  const modal = document.getElementById('appPathsModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

function setAppType(type) {
  state.selectedAppType = type;
  const btnSystem = document.getElementById('btnTypeSystem');
  const btnWeb = document.getElementById('btnTypeWeb');
  if (type === 'system') {
    btnSystem.classList.add('active');
    btnWeb.classList.remove('active');
  } else {
    btnWeb.classList.add('active');
    btnSystem.classList.remove('active');
  }
}

async function addAppPath() {
  const nameInput = document.getElementById('appName');
  const pathInput = document.getElementById('appPath');
  const name = nameInput.value.trim();
  const pathOrUrl = pathInput.value.trim();

  if (!name || !pathOrUrl) {
    // Flash the empty inputs
    if (!name) nameInput.style.borderColor = 'rgba(255, 82, 82, 0.5)';
    if (!pathOrUrl) pathInput.style.borderColor = 'rgba(255, 82, 82, 0.5)';
    setTimeout(() => {
      nameInput.style.borderColor = '';
      pathInput.style.borderColor = '';
    }, 1500);
    return;
  }

  if (typeof eel !== 'undefined' && typeof eel.add_app_path === 'function') {
    try {
      const result = await eel.add_app_path(name, pathOrUrl, state.selectedAppType)();
      if (result) {
        nameInput.value = '';
        pathInput.value = '';
        loadAppPaths();
      }
    } catch (e) {
      console.error('Failed to add app path:', e);
    }
  } else {
    console.warn('eel.add_app_path is not available');
  }
}

async function loadAppPaths() {
  const listEl = document.getElementById('savedPathsList');
  const countEl = document.getElementById('pathCount');

  if (typeof eel === 'undefined' || typeof eel.get_all_app_paths !== 'function') {
    console.warn('eel.get_all_app_paths is not available');
    return;
  }

  try {
    const paths = await eel.get_all_app_paths()();
    countEl.textContent = paths.length;

    if (paths.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          <p>No paths added yet</p>
        </div>`;
      return;
    }

    listEl.innerHTML = paths.map((item, i) => `
      <div class="path-item" style="animation-delay: ${i * 0.05}s">
        <span class="path-type-badge ${item.type}">${item.type === 'system' ? 'SYS' : 'WEB'}</span>
        <div class="path-info">
          <div class="path-name" title="${item.name}">${item.name}</div>
          <div class="path-value" title="${item.path}">${item.path}</div>
        </div>
        <button class="path-delete-btn" onclick="deleteAppPath(${item.id}, '${item.type}')" title="Delete">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load app paths:', e);
  }
}

async function deleteAppPath(id, type) {
  if (typeof eel !== 'undefined' && typeof eel.delete_app_path === 'function') {
    try {
      const result = await eel.delete_app_path(id, type)();
      if (result) {
        loadAppPaths();
      }
    } catch (e) {
      console.error('Failed to delete app path:', e);
    }
  }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  const appModal = document.getElementById('appPathsModal');
  const contactsModal = document.getElementById('contactsModal');
  if (e.target === appModal) closeAppPaths();
  if (e.target === contactsModal) closeContacts();
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeAppPaths();
    closeContacts();
  }
});

// ═══════════════════════════════════════════════════════════════
//  WAKE WORD MODE — Continuous Loop
// ═══════════════════════════════════════════════════════════════

async function wakeWordContinuousLoop() {
  const requestId = ++activeListenRequestId;

  if (typeof eel === 'undefined' || typeof eel.listenForWakeWord !== 'function') {
    updateSpokenCommand('Voice service is not connected.');
    updateResponse('Cannot connect to voice backend.');
    setListeningVisualState(false);
    return;
  }

  while (state.isListening && state.mode === 'wakeword' && requestId === activeListenRequestId) {
    try {
      // Phase 1: Listen for wake word "Hey Sunday"
      updateSpokenCommand('Listening for "Hey Sunday"...');
      updateResponse('Say "Hey Sunday" to activate...');
      setStatus('wakeword');

      const result = await eel.listenForWakeWord()();

      if (!state.isListening || requestId !== activeListenRequestId) break;

      // Handle dict responses from updated backend
      const status = (typeof result === 'object') ? result.status : result;
      const capturedCommand = (typeof result === 'object') ? (result.command || '') : '';

      if (status === '__MUTED__') {
        updateSpokenCommand('Mic is muted.');
        updateResponse('Unmute to use wake word mode.');
        setListeningVisualState(false);
        return;
      }
      if (status === '__PAUSED__') {
        updateSpokenCommand('Assistant is paused.');
        updateResponse('Resume to use wake word mode.');
        setListeningVisualState(false);
        return;
      }

      if (status !== 'detected') {
        // Voice was heard but wasn't wake word — show feedback
        const heardText = (typeof result === 'object') ? (result.heard || '') : '';
        if (heardText) {
          updateSpokenCommand(`"${heardText}"`);
          updateResponse('Not the wake word. Say "Hey Sunday"…');
          await showCooldownCountdown(COOLDOWN_SECONDS);
          // Restore listening state for next loop iteration
          if (state.isListening && requestId === activeListenRequestId) {
            setListeningVisualState(true);
            updateSpokenCommand('Listening for "Hey Sunday"...');
            updateResponse('Say "Hey Sunday" to activate...');
          }
        }
        continue;
      }

      // Phase 2: Wake word detected! Acknowledgment already spoken by backend
      updateSpokenCommand('🎯 Hey Sunday detected!');
      updateResponse('Processing your command...');
      setStatus('listening');
      setCurrentTask('Awaiting command…', 'running');

      let query = '';

      if (capturedCommand) {
        // Command was spoken together with wake word — process it directly!
        console.log('[WakeWord] Command captured with wake word:', capturedCommand);
        setStatus('thinking');
        updateResponse('Processing...');
        query = await eel.processCommand(capturedCommand)();
      } else {
        // No command in the wake word phrase — listen for a separate command
        updateResponse('Listening for your command...');
        setStatus('listening');

        // Brief pause to let the user start speaking
        await new Promise(resolve => setTimeout(resolve, 300));

        setStatus('thinking');
        updateResponse('Processing...');
        query = await eel.allCommands()();
      }

      if (!state.isListening || requestId !== activeListenRequestId) break;

      // Phase 3: Display results
      if (query === '__PAUSED__') {
        updateSpokenCommand('Assistant is paused.');
        updateResponse('Resume the assistant to process commands.');
        setCurrentTask('Paused', 'failed');
        setTimeout(clearCurrentTask, 3000);
        setListeningVisualState(false);
        return;
      }

      if (query && query.trim()) {
        updateSpokenCommand(query.trim());
        if (query.includes('send message') || query.includes('whatsapp') || query.includes('send whatsapp')) {
          updateResponse('Sending WhatsApp message...');
          setCurrentTask('Sending WhatsApp message', 'completed');
        } else if (query.includes('open')) {
          const appName = query.replace('sunday', '').replace('hey', '').replace('open', '').trim();
          updateResponse(`Opening ${appName}...`);
          setCurrentTask(`Opening ${appName}`, 'completed');
        } else if (query.includes('on youtube')) {
          updateResponse('Playing on YouTube...');
          setCurrentTask('Playing on YouTube', 'completed');
        } else {
          updateResponse('Command not recognized. Please try again.');
          setCurrentTask('Unrecognized command', 'failed');
        }
        setTimeout(clearCurrentTask, 5000);
      } else {
        updateSpokenCommand("Couldn't catch that. Try again.");
        updateResponse('No command detected. Listening again...');
        clearCurrentTask();
      }

      // ── Cooldown before next wake word listen ──
      if (query && query.trim()) {
        await showCooldownCountdown(COOLDOWN_SECONDS);
      } else {
        // Short pause for no-command case
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Restore listening visual state — wake word loop is still running
      if (state.isListening && requestId === activeListenRequestId) {
        setListeningVisualState(true);
      }

    } catch (error) {
      console.error('Wake word loop error:', error);
      updateSpokenCommand('Error occurred. Retrying...');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  // Loop ended (user clicked stop)
  if (requestId === activeListenRequestId) {
    setListeningVisualState(false);
    updateSpokenCommand('Tap the mic and say your command...');
    updateResponse('Waiting for your command...');
    setStatus('idle');
  }
}

// ── Mode Toggle ──────────────────────────────────────────────
function setMode(newMode) {
  // If currently listening, stop first
  if (state.isListening) {
    activeListenRequestId++;
    state.isListening = false;
    setListeningVisualState(false);
  }

  state.mode = newMode;
  const btnManual = document.getElementById('btnManual');
  const btnWakeWord = document.getElementById('btnWakeWord');

  if (newMode === 'manual') {
    if (btnManual) btnManual.classList.add('active');
    if (btnWakeWord) btnWakeWord.classList.remove('active');
    updateSpokenCommand('Tap the mic and say your command...');
    updateResponse('Manual mode — tap mic for each command');
  } else {
    if (btnWakeWord) btnWakeWord.classList.add('active');
    if (btnManual) btnManual.classList.remove('active');
    updateSpokenCommand('Tap the mic to start wake word listening');
    updateResponse('Wake word mode — say "Hey Sunday" to activate');
  }
  setStatus('idle');
}

// ═══════════════════════════════════════════════════════════════
//  CONTACTS MODAL
// ═══════════════════════════════════════════════════════════════

function openContacts() {
  const modal = document.getElementById('contactsModal');
  if (modal) {
    modal.classList.remove('hidden');
    loadContacts();
  }
}

function closeContacts() {
  const modal = document.getElementById('contactsModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

async function addContact() {
  const nameInput = document.getElementById('contactName');
  const phoneInput = document.getElementById('contactPhone');
  const name = nameInput.value.trim();
  const phone = phoneInput.value.trim();

  if (!name || !phone) {
    if (!name) nameInput.style.borderColor = 'rgba(255, 82, 82, 0.5)';
    if (!phone) phoneInput.style.borderColor = 'rgba(255, 82, 82, 0.5)';
    setTimeout(() => {
      nameInput.style.borderColor = '';
      phoneInput.style.borderColor = '';
    }, 1500);
    return;
  }

  // Validate phone starts with +
  if (!phone.startsWith('+')) {
    phoneInput.style.borderColor = 'rgba(255, 82, 82, 0.5)';
    phoneInput.value = '';
    phoneInput.placeholder = 'Must start with + (e.g. +91...)';
    setTimeout(() => {
      phoneInput.style.borderColor = '';
      phoneInput.placeholder = '+919876543210';
    }, 2500);
    return;
  }

  if (typeof eel !== 'undefined' && typeof eel.add_contact === 'function') {
    try {
      const result = await eel.add_contact(name, phone)();
      if (result) {
        nameInput.value = '';
        phoneInput.value = '';
        loadContacts();
      }
    } catch (e) {
      console.error('Failed to add contact:', e);
    }
  } else {
    console.warn('eel.add_contact is not available');
  }
}

async function loadContacts() {
  const listEl = document.getElementById('savedContactsList');
  const countEl = document.getElementById('contactCount');

  if (typeof eel === 'undefined' || typeof eel.get_all_contacts !== 'function') {
    console.warn('eel.get_all_contacts is not available');
    return;
  }

  try {
    const contacts = await eel.get_all_contacts()();
    countEl.textContent = contacts.length;

    if (contacts.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
          </svg>
          <p>No contacts added yet</p>
        </div>`;
      return;
    }

    listEl.innerHTML = contacts.map((c, i) => `
      <div class="path-item contact-item" style="animation-delay: ${i * 0.05}s">
        <span class="path-type-badge whatsapp">WA</span>
        <div class="path-info">
          <div class="path-name" title="${c.name}">${c.name}</div>
          <div class="path-value" title="${c.phone}">${c.phone}</div>
        </div>
        <button class="path-delete-btn" onclick="deleteContact(${c.id})" title="Delete">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load contacts:', e);
  }
}

async function deleteContact(id) {
  if (typeof eel !== 'undefined' && typeof eel.delete_contact === 'function') {
    try {
      const result = await eel.delete_contact(id)();
      if (result) {
        loadContacts();
      }
    } catch (e) {
      console.error('Failed to delete contact:', e);
    }
  }
}

// ═══════════════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  setStatus('idle');
  animFrame = requestAnimationFrame(drawVisualizer);
  renderCurrentTask();
});
