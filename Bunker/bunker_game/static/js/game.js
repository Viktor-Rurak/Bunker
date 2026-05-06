const socket = io();

// ── STATE ──
let myName          = sessionStorage.getItem('player_name') || 'Гравець';
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
  socket.emit('join_room', { code: ROOM_CODE, name: myName });
});

socket.on('error', data => {
  addLog('⚠ ' + data.msg, 'danger');
  if (!gameStarted) {
    document.getElementById('lobby-status').textContent = data.msg;
  }
});

socket.on('joined', data => {
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
socket.on('round_update', data => {
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
  const grid = document.getElementById('players-grid');
  grid.innerHTML = '';

  players.forEach(p => {
    const totalHidden   = p.total_characteristics - p.revealed.length;
    const revealedChips = p.revealed.map(c => `
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
