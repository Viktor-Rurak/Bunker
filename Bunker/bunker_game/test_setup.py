"""
test_setup.py — швидке налаштування тестової гри

Що робить:
  1. Реєструє акаунти test1..test6 (якщо вже є — просто логіниться)
  2. test1 створює кімнату
  3. Виводить код кімнати і дані для входу

Запуск:
  python test_setup.py
  python test_setup.py --url http://localhost:5000
  python test_setup.py --url https://your-app.railway.app
"""

import sys
import argparse
import requests

# ── Налаштування ──────────────────────────────────────────────────────────────

TEST_USERS = [
    {"username": f"test{i}", "password": "test1234"}
    for i in range(1, 7)
]


# ── Функції ───────────────────────────────────────────────────────────────────

def login_or_register(base_url: str, username: str, password: str) -> requests.Session:
    s = requests.Session()

    # Спочатку пробуємо залогінитись
    r = s.post(f"{base_url}/api/login", json={"username": username, "password": password})
    if r.status_code == 200 and r.json().get("ok"):
        print(f"  ✓ {username} — увійшов")
        return s

    # Якщо акаунту немає — реєструємо
    r = s.post(f"{base_url}/api/register", json={"username": username, "password": password})
    if r.status_code == 200 and r.json().get("ok"):
        print(f"  ✓ {username} — зареєстровано і увійшов")
        return s

    # Щось пішло не так
    print(f"  ✗ {username} — помилка: {r.text}")
    sys.exit(1)


def create_room(base_url: str, session: requests.Session) -> str:
    r = session.post(f"{base_url}/api/create_room", json={})
    if r.status_code == 200:
        code = r.json()["code"]
        print(f"  ✓ Кімната створена: {code}")
        return code
    print(f"  ✗ Не вдалося створити кімнату: {r.text}")
    sys.exit(1)


# ── Головна логіка ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000",
                        help="URL сервера (default: http://localhost:5000)")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"\n{'='*55}")
    print(f"  БУНКЕР — тестове налаштування")
    print(f"  Сервер: {base}")
    print(f"{'='*55}\n")

    # 1. Логін / реєстрація всіх акаунтів
    print("[ 1/2 ] Акаунти:")
    sessions = []
    for u in TEST_USERS:
        s = login_or_register(base, u["username"], u["password"])
        sessions.append(s)

    # 2. test1 створює кімнату
    print("\n[ 2/2 ] Створення кімнати (test1):")
    code = create_room(base, sessions[0])

    # 3. Виводимо інструкції
    print(f"\n{'='*55}")
    print(f"  КОД КІМНАТИ:  {code}")
    print(f"{'='*55}")
    print(f"\n  Відкрий 6 вікон/вкладок у браузері та увійди:")
    print()
    for u in TEST_USERS:
        tag = " ← вже в кімнаті (хост)" if u["username"] == "test1" else ""
        print(f"    {u['username']:8s}  пароль: {u['password']}{tag}")
    print()
    print(f"  URL входу:  {base}/auth")
    print(f"  URL кімнати: {base}/room/{code}")
    print()
    print("  Порада: відкривай кожне вікно в окремому профілі або")
    print("  використовуй режим інкогніто щоб сесії не перетиналися.")
    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
