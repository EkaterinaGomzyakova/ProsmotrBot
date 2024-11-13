import sqlite3

# Создание подключения к базе данных
def create_connection():
    return sqlite3.connect("subscriptions.db")

# Создание таблиц (вызывается один раз при инициализации)
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL
        )
    ''')

    # Таблица подписок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            direction TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица мероприятий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            city TEXT NOT NULL,
            type TEXT,
            date TEXT,
            is_approved INTEGER DEFAULT 0  -- 0 - не одобрено, 1 - одобрено
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

# Добавление подписки
def add_subscription(user_id, city, direction):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO subscriptions (user_id, city, direction)
        VALUES (?, ?, ?)
    ''', (user_id, city, direction))
    conn.commit()
    conn.close()

# Получение подписок пользователя
def get_subscriptions(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT city, direction FROM subscriptions WHERE user_id = ?', (user_id,))
    subscriptions = cursor.fetchall()
    conn.close()

    return subscriptions

# Обновление подписки
def update_subscription(user_id, old_city, old_direction, new_city, new_direction):
    conn = create_connection()
    cursor = conn.cursor()
    
    # Обновляем подписку в базе данных
    cursor.execute('''
        UPDATE subscriptions 
        SET city = ?, direction = ? 
        WHERE user_id = ? AND city = ? AND direction = ?
    ''', (new_city, new_direction, user_id, old_city, old_direction))
    
    conn.commit()
    conn.close()
