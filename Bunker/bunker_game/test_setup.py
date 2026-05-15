"""
test_setup.py — автоматичне налаштування тестової гри

Що робить:
  1. Реєструє/логінить test1..test6
  2. test1 створює кімнату
  3. Отримує одноразові токени для кожного гравця
  4. Відкриває 6 незалежних Chrome вікон — кожне вже залогінене і в кімнаті
  5. Тобі залишається лише натиснути «Старт» у вікні test1

Вимоги:
  pip install requests
  Додай DEV_SECRET=test-secret в Railway Variables (або .env локально)

Запуск:
  python test_setup.py --url https://your-app.railway.app --dev-secret test-secret
"""

import sys
import os
import time
import argparse
import subprocess
import tempfile
import requests

# ── Налаштування ──────────────────────────────────────────────────────────────

TEST_USERS = [
    {"username": f"test{i}", "password": "test1234"}
    for i in range(1, 7)
]

# ── Пошук Chrome ─────────────────────────────────────────────────────────────

def find_chrome():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
            os.environ.get("USERNAME", "")
        ),
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Пробуємо через PATH
    import shutil
    return shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")


def open_chrome_window(chrome_path, url, profile_dir):
    """Відкриває Chrome з окремим профілем — незалежна сесія."""
    subprocess.Popen([
        chrome_path,
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── HTTP функції ──────────────────────────────────────────────────────────────

def login_or_register(base_url, username, password):
    s = requests.Session()
    r = s.post(f"{base_url}/api/login", json={"username": username, "password": password})
    if r.status_code == 200 and r.json().get("ok"):
        print(f"  ✓ {username} — увійшов")
        return s
    r = s.post(f"{base_url}/api/register", json={"username": username, "password": password})
    if r.status_code == 200 and r.json().get("ok"):
        print(f"  ✓ {username} — зареєстровано і увійшов")
        return s
    print(f"  ✗ {username} — помилка: {r.text}")
    sys.exit(1)


def create_room(base_url, session):
    r = session.post(f"{base_url}/api/create_room", json={})
    if r.status_code == 200:
        code = r.json()["code"]
        print(f"  ✓ Кімната створена: {code}")
        return code
    print(f"  ✗ Не вдалося створити кімнату: {r.text}")
    sys.exit(1)


def get_autologin_url(base_url, dev_secret, username, password):
    r = requests.post(
        f"{base_url}/api/dev/token",
        json={"username": username, "password": password},
        headers={"X-Dev-Secret": dev_secret},
    )
    if r.status_code == 200:
        token = r.json()["token"]
        return f"{base_url}/dev/login/{token}"
    print(f"  ✗ Не вдалося отримати токен для {username}: {r.text}")
    sys.exit(1)


# ── Головна логіка ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000")
    parser.add_argument("--dev-secret", default="test-secret",
                        help="DEV_SECRET з Railway Variables")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"\n{'='*55}")
    print(f"  БУНКЕР — автозапуск тестової гри")
    print(f"  Сервер: {base}")
    print(f"{'='*55}\n")

    # 1. Акаунти
    print("[ 1/4 ] Акаунти:")
    for u in TEST_USERS:
        login_or_register(base, u["username"], u["password"])

    # 2. Кімната
    print("\n[ 2/4 ] Кімната (test1):")
    host_session = requests.Session()
    r = host_session.post(f"{base}/api/login",
                          json={"username": "test1", "password": "test1234"})
    code = create_room(base, host_session)

    # 3. Токени
    print("\n[ 3/4 ] Токени автологіну:")
    urls = []
    for u in TEST_USERS:
        url = get_autologin_url(base, args.dev_secret, u["username"], u["password"])
        print(f"  ✓ {u['username']}")
        urls.append(url)

    # 4. Відкриваємо Chrome вікна
    print("\n[ 4/4 ] Відкриваємо Chrome:")
    chrome = find_chrome()
    if not chrome:
        print("  ✗ Chrome не знайдено! Відкрий вручну:")
        for u, url in zip(TEST_USERS, urls):
            print(f"    {u['username']}: {url}")
        sys.exit(1)

    tmp_base = tempfile.gettempdir()
    for i, (u, url) in enumerate(zip(TEST_USERS, urls)):
        profile_dir = os.path.join(tmp_base, f"bunker_test_profile_{i+1}")
        open_chrome_window(chrome, url, profile_dir)
        print(f"  ✓ {u['username']} — вікно відкрито")
        time.sleep(0.5)   # невелика пауза щоб вікна не злились

    print(f"\n{'='*55}")
    print(f"  Готово! Код кімнати: {code}")
    print(f"  У вікні test1 натисни «Старт» щоб почати гру.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
