function toggleMenu() {
  document.getElementById('nav-links').classList.toggle('open');
}

function abrirModalDev() {
  document.getElementById('modal-dev').classList.add('open');
  document.getElementById('input-password').value = '';
  document.getElementById('modal-error').textContent = '';
  setTimeout(() => document.getElementById('input-password').focus(), 100);
}

function cerrarModalDev(e) {
  if (!e || e.target === document.getElementById('modal-dev')) {
    document.getElementById('modal-dev').classList.remove('open');
  }
}

async function verificarPassword() {
  const password = document.getElementById('input-password').value;
  const errorEl = document.getElementById('modal-error');
  errorEl.textContent = '';

  const r = await fetch('/api/dev/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  const data = await r.json();

  if (data.ok) {
    document.getElementById('modal-dev').classList.remove('open');
    document.getElementById('nav-dev-sep').style.display = 'flex';
    document.getElementById('nav-dev-links').style.display = 'flex';
    document.getElementById('btn-dev').textContent = '⚙️ Programador';
    document.getElementById('btn-dev').style.background = 'linear-gradient(135deg, #06d6a0, #059669)';
    document.getElementById('btn-dev').onclick = () => window.location.href = '/dev';
  } else {
    errorEl.textContent = data.error || 'Contraseña incorrecta';
    document.getElementById('input-password').focus();
  }
}
