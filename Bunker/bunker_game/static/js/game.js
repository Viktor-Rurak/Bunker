const socket = io();

// ── STATE ──
let myName          = typeof MY_USERNAME !== 'undefined' ? MY_USERNAME : 'Гравець';
let mySid           = null;
let isHost          = false;
let myCard          = null;
let revealedByMe    = [];
let revealsAllowed  = 0;
let revealsThisRound = 0;
let currentRound    = 0;
let hasVoted        = false;
let gameStarted     = false;

// ── CONNECT ──
socket.on('connect', () => {
  console.log('[SOCKET] connected, emitting join_room with code:', ROOM_CODE);
  socket.emit('join_room', { code: ROOM_CODE });
});

socket.on('connect_error', (err) => {
  console.error('[SOCKET] connect_error:', err.message);
  document.getElementById('lobby-status').textContent = 'Помилка з\'єднання: ' + err.message;
});

socket.on('disconnect', (reason) => {
  console.warn('[SOCKET] disconnected:', reason);
});

// ── LEAVE GAME ──
async function leaveGame() {
  if (!confirm('Вийти з гри та повернутись на головну?')) return;
  await fetch('/api/leave_game', { method: 'POST' });
  window.location.href = '/';
};

socket.on('join_error', data => {
  console.error('[SOCKET] join_error:', data.msg);
  addLog('⚠ ' + data.msg, 'danger');
  if (!gameStarted) {
    document.getElementById('lobby-status').textContent = data.msg;
  }
});

// keep legacy error listener too
socket.on('error', data => {
  if (data && data.msg) {
    addLog('⚠ ' + data.msg, 'danger');
    if (!gameStarted) {
      document.getElementById('lobby-status').textContent = data.msg;
    }
  }
});

socket.on('joined', data => {
  console.log('[SOCKET] joined:', data);
  mySid   = data.sid;
  isHost  = data.is_host;
  document.getElementById('lobby-status').textContent =
    isHost ? 'Ви хост. Почекайте гравців.' : 'Очікуємо початку гри...';
  if (isHost) document.getElementById('start-btn').disabled = false;
});

socket.on('lobby_update', data => {
  const list = document.getElementById('lobby-player-list');
  list.innerHTML = data.players.map(p => `
    <div class="lobby-player">
      <div class="dot"></div>
      <span>${p.name}</span>
      ${p.is_host ? '<span class="tag tag-host">ХОСТ</span>' : ''}
    </div>
  `).join('');
  if (isHost) document.getElementById('start-btn').disabled = data.players.length < 2;
});

socket.on('player_left', data => addLog(`${data.name} покинув кімнату`, 'highlight'));

socket.on('player_reconnected', data => {
  addLog(`${data.name} перепідключився`, 'highlight');
});

// ── GAME START ──
socket.on('game_started', data => {
  
  gameStarted      = true;
  myCard           = data.my_card;
  currentRound     = data.round;
  revealsAllowed   = data.reveals_this_round;
  revealsThisRound = 0;

  document.getElementById('lobby-screen').style.display = 'none';
  document.getElementById('my-card-panel').style.display = 'block';

  showGameInfo(data.game_info);
  renderMyCard();
  renderAllPlayers(data.all_players);
  updateRoundBadge();

  myActionCards = data.my_card.action_cards || [];
  renderActionCards();
  addLog('Гра почалась!', 'highlight');
  addLog(`Катастрофа: ${data.game_info.catastrophe.name}`, 'danger');
  addLog(`Раунд 1 — відкрийте ${revealsAllowed} характеристик`, 'highlight');
});

// ── REVEAL ──
socket.on('player_revealed', data => {
  addLog(
    `${data.name} відкрив: ${data.icon} ${data.label} — ${data.value}`,
    data.sid === mySid ? 'highlight' : ''
  );

  const card = document.querySelector(`.player-card[data-sid="${data.sid}"]`);
  if (!card) return;

  const chars     = card.querySelector('.characteristics');
  const hiddenChip = chars.querySelector('.hidden-chip');
  if (hiddenChip) hiddenChip.remove();

  const chip = document.createElement('div');
  chip.className = 'char-chip just-revealed';
  chip.innerHTML = `
    <span class="chip-icon">${data.icon}</span>
    <div>
      <div class="chip-label">${data.label}</div>
      <div>${data.value}</div>
    </div>`;
  chars.appendChild(chip);
  setTimeout(() => chip.classList.remove('just-revealed'), 600);
});

// ── VOTING ──
socket.on('voting_started', data => {
  hasVoted = false;
  document.getElementById('voting-overlay').classList.add('show');
  document.getElementById('voting-subtitle').textContent = `РАУНД ${data.round} — КОГО ВИГНАТИ?`;

  document.getElementById('vote-options').innerHTML = data.players
    .filter(p => p.sid !== mySid)
    .map(p => `<button class="vote-btn" onclick="castVote('${p.sid}', this)">${p.name}</button>`)
    .join('');

  document.getElementById('vote-progress').textContent = 'Очікуємо голосів...';
});

socket.on('vote_update', data => {
  document.getElementById('vote-progress').textContent =
    `Проголосувало: ${data.votes_cast} / ${data.votes_needed}`;
});

// ── KICK ──
socket.on('player_kicked', data => {
  document.getElementById('voting-overlay').classList.remove('show');
  document.getElementById('kick-name').textContent = data.name;
  document.getElementById('kick-votes-detail').textContent =
    Object.entries(data.tally).map(([n, v]) => `${n}: ${v} голос(ів)`).join(' | ');
  document.getElementById('kick-overlay').classList.add('show');
  addLog(`${data.name} вигнано з бункера`, 'danger');

  const card = document.querySelector(`.player-card[data-sid="${data.sid}"]`);
  if (card) card.classList.add('kicked');
});

// ── NEXT ROUND ──
socket.on('new_round', data => {
  currentRound     = data.round;
  revealsAllowed   = data.reveals_this_round;
  revealsThisRound = 0;
  updateRoundBadge();
  renderAllPlayers(data.all_players);
  renderMyCard();
  addLog(`Раунд ${data.round + 1} — відкрийте ${revealsAllowed} характеристик`, 'highlight');
});

// ── GAME OVER ──
socket.on('game_over', data => {
  const overlay = document.getElementById('gameover-overlay');
  const title   = document.getElementById('gameover-title');
  const sub     = document.getElementById('gameover-sub');
  const list    = document.getElementById('survivor-list');
  const summary = document.getElementById('points-summary');

  overlay.classList.add('show');
  title.textContent  = data.survived ? 'ВИЖИЛИ!' : 'ЗАГИНУЛИ';
  title.className    = 'gameover-title ' + (data.survived ? 'survived' : 'dead');
  sub.textContent    = data.survived
    ? 'Команда набрала достатньо балів для виживання'
    : 'Команда не змогла вижити в бункері';

  list.innerHTML = data.survivors
    .map((s, i) => `
      <div class="survivor-item">
        <span class="s-name">${i + 1}. ${s.name}</span>
        <span class="s-pts">${s.points} балів</span>
      </div>`)
    .join('');

  summary.innerHTML =
    `Бали команди: <span>${data.total_points}</span> / Поріг бункера: <span>${data.bunker_points}</span>`;

  // Запрошуємо генерацію історії
  generateStory(data);
});

// ── STORY ──
socket.on('story_ready', data => {
  const block = document.getElementById('story-block');
  document.getElementById('story-loading').style.display = 'none';
  document.getElementById('story-text').textContent = data.story;
  block.style.display = 'block';
});

// ── ACTIONS ──
function startGame() {
  socket.emit('start_game', { code: ROOM_CODE });
}

function revealCharacteristic(key) {
  if (revealsThisRound >= revealsAllowed) return;
  if (revealedByMe.includes(key)) return;
  socket.emit('reveal_characteristic', { code: ROOM_CODE, key });
  revealedByMe.push(key);
  revealsThisRound++;
  renderMyCard();
}

function castVote(targetSid, btn) {
  if (hasVoted) return;
  hasVoted = true;
  document.querySelectorAll('.vote-btn').forEach(b => { b.disabled = true; });
  btn.classList.add('voted');
  socket.emit('vote', { code: ROOM_CODE, target: targetSid });
}

function closeKickOverlay() {
  document.getElementById('kick-overlay').classList.remove('show');
}

function copyCode() {
  navigator.clipboard.writeText(ROOM_CODE);
  addLog('Код скопійовано в буфер обміну');
}

function generateStory(gameData) {
  document.getElementById('story-loading').style.display = 'block';
  socket.emit('generate_story', { code: ROOM_CODE });
}

// ── RENDER ──
function showGameInfo(info) {
  document.getElementById('catastrophe-panel').style.display = 'block';
  document.getElementById('bunker-panel').style.display = 'block';
  document.getElementById('cat-name').textContent  = info.catastrophe.name;
  document.getElementById('cat-desc').textContent  = info.catastrophe.description;

  document.getElementById('bunker-info').innerHTML = `
    <div class="bunker-item"><div class="dot"></div>${info.bunker.size}</div>
    ${info.bunker.items.map(i => `<div class="bunker-item"><div class="dot"></div>${i}</div>`).join('')}
    <div class="bunker-item"><div class="dot"></div>${info.bunker.time}</div>
  `;
}

function renderAllPlayers(players) {
  currentAllPlayers = players;
  const grid = document.getElementById('players-grid');
  grid.innerHTML = '';

  players.forEach(p => {
    const totalChars    = p.total_characteristics || 10;
    const totalHidden   = Math.max(0, totalChars - (p.revealed || []).length);
    const revealedChips = (p.revealed || []).map(c => `
      <div class="char-chip">
        <span class="chip-icon">${c.icon}</span>
        <div><div class="chip-label">${c.label}</div><div>${c.value}</div></div>
      </div>`).join('');
    const hiddenChips = Array(totalHidden).fill(0).map(() =>
      `<div class="char-chip hidden-chip"><span class="chip-icon">?</span><div><div class="chip-label">закрито</div></div></div>`
    ).join('');

    const card = document.createElement('div');
    card.className   = `player-card${p.is_me ? ' is-me' : ''}`;
    card.dataset.sid = p.sid;
    card.innerHTML   = `
      <div class="player-card-header">
        <div class="player-name">${p.name}</div>
        <div style="display:flex;gap:0.3rem;align-items:center">
          ${p.is_host ? '<span class="tag tag-host">ХОСТ</span>' : ''}
          ${p.is_me   ? '<span class="tag tag-me">ВИ</span>'   : ''}
        </div>
      </div>
      <div class="characteristics">${revealedChips}${hiddenChips}</div>`;
    grid.appendChild(card);
  });
}

function renderMyCard() {
  if (!myCard) return;

  const canRevealMore = revealsThisRound < revealsAllowed;
  document.getElementById('reveal-hint').style.display = canRevealMore ? 'block' : 'none';
  document.getElementById('reveal-counter').innerHTML  =
    `Відкрито в цьому раунді: <span>${revealsThisRound}/${revealsAllowed}</span>`;

  document.getElementById('my-char-list').innerHTML = myCard.characteristics.map(c => {
    const isRevealed = revealedByMe.includes(c.key);
    const canReveal  = !isRevealed && canRevealMore;
    const statusText = isRevealed ? 'ВІДКРИТО' : canReveal ? 'НАТИСНІТЬ' : 'ЗАКРИТО';
    const cls        = isRevealed ? 'revealed' : canReveal ? 'can-reveal' : 'locked';
    return `
      <div class="my-char ${cls}" onclick="${canReveal ? `revealCharacteristic('${c.key}')` : ''}">
        <div class="char-icon">${c.icon}</div>
        <div class="char-info">
          <div class="char-name">${c.label}</div>
          <div class="char-value">${c.value}</div>
        </div>
        <div class="char-status">${statusText}</div>
      </div>`;
  }).join('');
}

function updateRoundBadge() {
  document.getElementById('round-badge').textContent = `РАУНД ${currentRound + 1}`;
}

function addLog(text, type = '') {
  const log   = document.getElementById('event-log');
  const entry = document.createElement('div');
  entry.className = 'log-entry ' + type;
  const time  = new Date().toLocaleTimeString('uk', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  entry.textContent = `[${time}] ${text}`;
  log.prepend(entry);
}

// ── ACTION CARDS STATE ──
let myActionCards = [];
let myEliminationCard = null;
let currentAllPlayers = [];
let activeActionCard = null;
let activeIsElim = false;

const CHAR_LABELS = {
  occupation: '💼 Професія',
  body:       '🏃 Тілобудова',
  trait:      '🧠 Характер',
  health:     "❤️ Здоров'я",
  hobby:      '🎯 Хобі',
  phobia:     '😨 Фобія',
  item:       '🎒 Предмет',
  additional: '📋 Додаткова інфо',
};

// ── RENDER ACTION CARDS ──
function renderActionCards() {
  const section = document.getElementById('action-cards-section');
  const list    = document.getElementById('action-cards-list');
  if (!myActionCards.length) return;
  section.style.display = 'block';
  list.innerHTML = myActionCards.map((ac, i) => {
    const badge = ac.characteristic
      ? `<span class="ac-char-badge">${CHAR_LABELS[ac.characteristic] || ac.characteristic}</span>`
      : '';
    const desc = ac.description.length > 80
      ? ac.description.substring(0, 78) + '…'
      : ac.description;
    const usedClass = ac.used ? 'used' : 'available';
    const btn = ac.used
      ? '<div class="ac-desc" style="text-align:center;letter-spacing:.1em">ВИКОРИСТАНО</div>'
      : `<button class="ac-use-btn" onclick="openActionModal(${i},false)">[ ВИКОРИСТАТИ ]</button>`;
    return `<div class="action-card-item ${usedClass}">
      <div class="ac-header"><span class="ac-name">${ac.name}</span>${badge}</div>
      <div class="ac-desc">${desc}</div>${btn}</div>`;
  }).join('');
}

function renderEliminationCard() {
  const section = document.getElementById('elim-card-section');
  const cont    = document.getElementById('elim-card-container');
  if (!myEliminationCard) return;
  section.style.display = 'block';
  const ac = myEliminationCard;
  const desc = ac.description.length > 90
    ? ac.description.substring(0, 88) + '…'
    : ac.description;
  const usedClass = ac.used ? 'used' : 'available';
  const btn = ac.used
    ? '<div class="ac-desc" style="text-align:center;letter-spacing:.1em">ВИКОРИСТАНО</div>'
    : `<button class="ac-use-btn rv" onclick="openActionModal(0,true)">[ ЗАСТОСУВАТИ ПОМСТУ ]</button>`;
  cont.innerHTML = `<div class="action-card-item revenge ${usedClass}">
    <div class="ac-header"><span class="ac-name rv">${ac.name}</span></div>
    <div class="ac-desc">${desc}</div>${btn}</div>`;
}

// ── ACTION MODAL ──
function openActionModal(idx, isElim) {
  activeIsElim      = isElim;
  activeActionCard  = isElim ? myEliminationCard : myActionCards[idx];
  if (!activeActionCard || activeActionCard.used) return;

  const box = document.getElementById('action-modal-box');
  box.className = 'action-modal-box' + (isElim ? ' rv-modal' : '');

  const title = document.getElementById('am-title');
  title.textContent = activeActionCard.name;
  title.className   = 'am-title' + (isElim ? ' rv' : '');
  document.getElementById('am-desc').textContent = activeActionCard.description;

  buildModalContent(activeActionCard, idx, isElim);
  document.getElementById('action-modal-overlay').classList.add('show');
}

function buildModalContent(ac, idx, isElim) {
  const el = document.getElementById('am-content');

  if (ac.target === 'all') {
    el.innerHTML = `<div class="am-label">ДІЄ НА ВСІХ ГРАВЦІВ</div>
      <button class="am-target-btn"
        onclick="sendUseCard('${ac.name}',null,null,${isElim})">[ ПІДТВЕРДИТИ ]</button>`;
    return;
  }

  if (ac.target === 'self') {
    el.innerHTML = `<button class="am-target-btn"
      onclick="sendUseCard('${ac.name}',null,null,${isElim})">[ ПІДТВЕРДИТИ ]</button>`;
    return;
  }

  // single_choice — показуємо список гравців
  const targets = currentAllPlayers.filter(p => !p.kicked && p.sid !== mySid);
  if (!targets.length) {
    el.innerHTML = '<div class="am-label">НЕМАЄ ДОСТУПНИХ ЦІЛЕЙ</div>';
    return;
  }

  const needsChar = ['Детектив', 'Крадіжка'].includes(ac.name);

  el.innerHTML = `<div class="am-label">ОБЕРІТЬ ГРАВЦЯ:</div>` +
    targets.map(p => {
      const click = needsChar
        ? `showCharPicker('${ac.name}','${p.sid}','${p.name}',${isElim})`
        : `sendUseCard('${ac.name}','${p.sid}',null,${isElim})`;
      return `<button class="am-target-btn" onclick="${click}">${p.name}</button>`;
    }).join('');
}

function showCharPicker(cardName, targetSid, targetName, isElim) {
  const el = document.getElementById('am-content');
  const chars = Object.entries(CHAR_LABELS);
  el.innerHTML = `<div class="am-label">ХАРАКТЕРИСТИКА — ${targetName}:</div>` +
    chars.map(([k, l]) =>
      `<button class="am-char-btn"
        onclick="sendUseCard('${cardName}','${targetSid}','${k}',${isElim})">${l}</button>`
    ).join('');
}

function sendUseCard(cardName, targetSid, charKey, isElim) {
  socket.emit('use_action_card', {
    code: ROOM_CODE,
    card_name: cardName,
    target_sid: targetSid || null,
    characteristic_key: charKey || null,
    is_elimination: isElim,
  });
  closeActionModal();
}

function closeActionModal() {
  document.getElementById('action-modal-overlay').classList.remove('show');
  activeActionCard = null;
}

// ── SOCKET EVENTS ──
socket.on('got_elimination_card', data => {
  myEliminationCard = { ...data.card, used: false };
  renderEliminationCard();
  addLog('Отримано карту помсти: [' + data.card.name + ']', 'danger');
});

socket.on('action_card_result', data => {
  // Позначаємо карту як використану
  if (data.is_elimination) {
    if (myEliminationCard && myEliminationCard.name === data.card_name) {
      myEliminationCard.used = true;
      renderEliminationCard();
    }
  } else {
    const ac = myActionCards.find(c => c.name === data.card_name);
    if (ac) { ac.used = true; renderActionCards(); }
  }
  logActionResult(data);
});

socket.on('action_card_private', data => {
  if (data.type === 'anonymous_report') {
    document.getElementById('pr-title').textContent =
      'ДОСЬЄ: ' + data.target_name;
    document.getElementById('pr-chars').innerHTML =
      data.hidden_chars.map(c =>
        `<div class="pr-char"><span>${c.icon}</span>
         <span style="color:var(--muted)">${c.label}:</span>
         <span>${c.value}</span></div>`
      ).join('');
    document.getElementById('private-report-overlay').classList.add('show');
  }
});

socket.on('action_blocked', data => {
  addLog(
    data.user_name + ' → ' + data.card_name +
    ' — ЗАБЛОКОВАНО ' + data.blocker_name + ' (Імунітет)',
    'highlight'
  );
});

function logActionResult(data) {
  const e    = data.effect || {};
  const user = data.user_name;
  let msg = user + ' → ' + data.card_name;

  if (e.type === 'reveal') {
    msg += ': ' + e.target_name + ' [' + e.char_label + '] = ' + e.char_value;
    addLog(msg, 'highlight');
  } else if (e.type === 'betrayal') {
    msg += ': розкрито ' + e.revealed_count + ' карт ' + e.target_name;
    addLog(msg, 'danger');
  } else if (e.type === 'curse') {
    msg += ': ' + e.target_name + ' → ' + e.new_points + ' балів';
    addLog(msg, 'danger');
  } else if (e.type === 'enemy_bunker') {
    msg = '☢ ' + user + ' атакує! Штраф −' + e.penalty + ' балів кожному';
    addLog(msg, 'danger');
  } else if (e.type === 'swap') {
    msg += ': [' + e.char_label + '] з ' + e.target_name;
    addLog(msg, 'highlight');
  } else if (e.type === 'masquerade') {
    msg += ': обмін профессіями з ' + e.target_name;
    addLog(msg, 'highlight');
  } else if (e.type === 'alliance') {
    msg += ': союз з ' + e.target_name;
    addLog(msg, 'highlight');
  } else if (e.type === 'points_transfer') {
    msg += ': +' + e.amount + ' балів від ' + e.target_name;
    addLog(msg, 'highlight');
  } else if (e.type === 'immunity') {
    msg += ': імунітет активовано';
    addLog(msg, 'highlight');
  } else {
    addLog(msg, 'highlight');
  }
}
