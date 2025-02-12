import sqlite3

def create_connection():
    return sqlite3.connect("subscriptions.db")

# Создание таблиц
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            direction TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            city TEXT NOT NULL,
            direction TEXT,
            date TEXT,
            is_approved INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# Добавление пользователя
def add_user(telegram_id, full_name):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (telegram_id, full_name) VALUES (?, ?)', (telegram_id, full_name))
        conn.commit()

    conn.close()

# Получение user_id по telegram_id
def get_user_id(telegram_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()

    return user[0] if user else None

# Получение списка всех пользователей (для рассылки)
def get_all_users():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# Добавление подписки
def add_subscription(telegram_id, city, direction):
    user_id = get_user_id(telegram_id)
    if not user_id:
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO subscriptions (user_id, city, direction)
        VALUES (?, ?, ?)
    ''', (user_id, city, direction))
    conn.commit()
    conn.close()

# Получение подписчиков по фильтрам
def get_subscribers(city, direction):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.telegram_id FROM subscriptions 
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.city = ? AND subscriptions.direction = ?
    """, (city, direction))
    
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers
