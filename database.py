import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "subscriptions.db")

def create_connection():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """
    Создаёт таблицы users, subscriptions и events, если их ещё нет.
    Подписки и пользователи сохраняются между рестартами.
    """
    conn = create_connection()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      telegram_id INTEGER UNIQUE NOT NULL,
      full_name TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      event_city TEXT NOT NULL,
      event_direction TEXT NOT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_name TEXT NOT NULL,
      event_description TEXT,
      event_city TEXT NOT NULL,
      event_direction TEXT NOT NULL,
      event_date TEXT,             -- формат YYYY-MM-DD HH:MM
      is_approved INTEGER DEFAULT 0,
      notified_day_before INTEGER DEFAULT 0,
      notified_hour_before INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

def add_user(telegram_id, full_name):
    conn = create_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (telegram_id, full_name) VALUES (?, ?)",
        (telegram_id, full_name)
    )
    conn.commit()
    conn.close()

def get_all_users():
    """
    Возвращает список всех telegram_id из таблицы users.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r["telegram_id"] for r in rows]

def add_subscription(telegram_id, city, direction):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    if user:
        c.execute(
            "INSERT INTO subscriptions (user_id, event_city, event_direction) VALUES (?, ?, ?)",
            (user["id"], city, direction)
        )
        conn.commit()
    conn.close()

def get_subscriptions(telegram_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT event_city, event_direction
          FROM subscriptions
          JOIN users ON subscriptions.user_id = users.id
         WHERE users.telegram_id = ?
    """, (telegram_id,))
    rows = c.fetchall()
    conn.close()
    return [(r["event_city"], r["event_direction"]) for r in rows]

def get_events_by_filter(city, direction):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
         WHERE event_city = ?
           AND event_direction = ?
           AND is_approved = 1
    """, (city, direction))
    evts = [dict(r) for r in c.fetchall()]
    conn.close()
    return evts

def add_event(name, desc, city, direction, dt, is_approved=0):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO events
          (event_name, event_description, event_city, event_direction, event_date, is_approved)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, desc, city, direction, dt, is_approved))
    eid = c.lastrowid
    conn.commit()
    conn.close()
    return eid

def approve_event(event_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET is_approved = 1 WHERE id = ?", (event_id,))
    conn.commit()
    c.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def reject_event(event_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

def get_subscribers(city, direction):
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT users.telegram_id
          FROM subscriptions
          JOIN users ON subscriptions.user_id = users.id
         WHERE event_city = ?
           AND event_direction = ?
    """, (city, direction))
    subs = [r["telegram_id"] for r in c.fetchall()]
    conn.close()
    return subs

def get_events_for_day_reminder():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
         WHERE is_approved = 1
           AND notified_day_before = 0
           AND date(event_date) = date('now','+1 day')
    """)
    evts = [dict(r) for r in c.fetchall()]
    conn.close()
    return evts

def get_events_for_hour_reminder():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
         WHERE is_approved = 1
           AND notified_hour_before = 0
           AND date(event_date) = date('now')
           AND strftime('%s', event_date) <= strftime('%s','now','+1 hour')
           AND strftime('%s', event_date) > strftime('%s','now')
    """)
    evts = [dict(r) for r in c.fetchall()]
    conn.close()
    return evts

def mark_day_notified(event_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET notified_day_before = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

def mark_hour_notified(event_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET notified_hour_before = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
