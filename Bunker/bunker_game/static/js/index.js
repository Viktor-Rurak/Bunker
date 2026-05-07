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
