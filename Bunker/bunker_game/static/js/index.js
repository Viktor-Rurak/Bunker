async function createRoom() {
  const name = document.getElementById('create-name').value.trim();
  const err  = document.getElementById('create-error');
  err.classList.remove('show');

  if (!name) {
    err.textContent = 'Введіть ім\'я';
    err.classList.add('show');
    return;
  }

  const res  = await fetch('/api/create_room', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  });
  const data = await res.json();

  if (data.error) {
    err.textContent = data.error;
    err.classList.add('show');
    return;
  }

  sessionStorage.setItem('player_name', name);
  window.location.href = `/room/${data.code}`;
}

function joinRoom() {
  const name = document.getElementById('join-name').value.trim();
  const code = document.getElementById('join-code').value.trim().toUpperCase();
  const err  = document.getElementById('join-error');
  err.classList.remove('show');

  if (!name) {
    err.textContent = 'Введіть ім\'я';
    err.classList.add('show');
    return;
  }
  if (code.length !== 6) {
    err.textContent = 'Код має бути 6 символів';
    err.classList.add('show');
    return;
  }

  sessionStorage.setItem('player_name', name);
  window.location.href = `/room/${code}`;
}

document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const focused = document.activeElement;
  if (focused.id.startsWith('create')) createRoom();
  else if (focused.id.startsWith('join')) joinRoom();
});
