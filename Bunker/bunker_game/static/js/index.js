async function createRoom() {
  const err = document.getElementById('create-error');
  err.classList.remove('show');

  const res  = await fetch('/api/create_room', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await res.json();

  if (data.error) {
    err.textContent = data.error;
    err.classList.add('show');
    return;
  }
  window.location.href = `/room/${data.code}`;
}

function joinRoom() {
  const code = document.getElementById('join-code').value.trim().toUpperCase();
  const err  = document.getElementById('join-error');
  err.classList.remove('show');

  if (code.length !== 6) {
    err.textContent = 'Код має бути 6 символів';
    err.classList.add('show');
    return;
  }
  window.location.href = `/room/${code}`;
}

document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const focused = document.activeElement;
  if (focused && focused.id === 'join-code') joinRoom();
});

// ── ПОКАЗАТИ РЕЗУЛЬТАТИ ПІСЛЯ ГРИ ──
(function () {
  const raw = sessionStorage.getItem('gameResult');
  if (!raw) return;
  sessionStorage.removeItem('gameResult');

  let data;
  try { data = JSON.parse(raw); } catch { return; }
  const popup  = document.getElementById('gameover-popup');
  const title  = document.getElementById('go-title');
  const sub    = document.getElementById('go-sub');
  const list   = document.getElementById('go-list');
  const summary = document.getElementById('go-summary');

  title.textContent = data.survived ? 'ВИЖИЛИ!' : 'ЗАГИНУЛИ';
  title.style.color = data.survived ? '#4caf50' : '#c0392b';

  sub.textContent = data.survived
    ? 'Команда набрала достатньо балів для виживання'
    : 'Команда не змогла вижити в бункері';

  list.innerHTML = (data.survivors || []).map((s, i) => `
    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a2a1a;font-size:.75rem">
      <span style="color:#d4c9a8">${i + 1}. ${s.name}</span>
      <span style="color:#4caf50">${s.points} балів</span>
    </div>`).join('');

  summary.textContent =
    `Бали команди: ${data.total_points} / Поріг виживання: ${data.threshold}`;

  popup.style.display = 'flex';
})();

function closeGameoverPopup() {
  document.getElementById('gameover-popup').style.display = 'none';
}
