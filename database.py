import sqlite3

# Функция для создания подключения к БД с поддержкой именованных колонок
def create_connection():
    conn = sqlite3.connect("subscriptions.db")
    conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
    return conn

# Функция для пересоздания таблицы events с новыми именами столбцов
def recreate_events_table():
    conn = create_connection()
    cursor = conn.cursor()

    # Проверяем, есть ли нужные колонки
    cursor.execute("PRAGMA table_info(events)")
    columns = {column["name"] for column in cursor.fetchall()}

    if "event_city" not in columns:  # Если нет, пересоздаем таблицу
        print("Пересоздаем таблицу events с обновленными названиями столбцов...")

        cursor.execute("ALTER TABLE events RENAME TO old_events")

        cursor.execute('''
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_description TEXT,
                event_city TEXT NOT NULL,
                event_direction TEXT NOT NULL,
                event_date TEXT,
                is_approved INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            INSERT INTO events (id, event_name, event_description, event_city, event_direction, event_date, is_approved)
            SELECT id, event_name, event_description, city, direction, event_date, is_approved FROM old_events
        ''')

        cursor.execute("DROP TABLE old_events")
        conn.commit()
        print("Таблица events успешно обновлена.")

    conn.close()

# Создание таблиц (если их нет)
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
            event_city TEXT NOT NULL,
            event_direction TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_description TEXT,
            event_city TEXT NOT NULL,
            event_direction TEXT NOT NULL,
            event_date TEXT,
            is_approved INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

    recreate_events_table()

# Добавление мероприятия
def add_event(event_name, event_description, event_city, event_direction, event_date, is_approved=0):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO events (event_name, event_description, event_city, event_direction, event_date, is_approved)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (event_name, event_description, event_city, event_direction, event_date, is_approved))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return event_id

# Проверка наличия мероприятия по названию
def event_exists(event_name):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM events WHERE event_name = ?', (event_name,))
    event = cursor.fetchone()
    conn.close()
    
    return event is not None

# Получение всех мероприятий
def get_all_events():
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events")
    events = [dict(row) for row in cursor.fetchall()]  # Преобразуем в список словарей
    conn.close()
    return events

# Получение мероприятий по фильтрам
def get_events_by_filter(event_city, event_direction):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM events 
        WHERE event_city = ? AND event_direction = ? AND is_approved = 1
    """, (event_city, event_direction))
    
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events

# Получение подписчиков по фильтрам (город + направление)
def get_subscribers(event_city, event_direction):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT users.telegram_id FROM subscriptions 
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.event_city = ? AND subscriptions.event_direction = ?
    """, (event_city, event_direction))
    
    subscribers = [row["telegram_id"] for row in cursor.fetchall()]
    conn.close()
    
    return subscribers



# Подтверждение мероприятия (изменение is_approved на 1)
def approve_event(event_id):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE events SET is_approved = 1 WHERE id = ?", (event_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    
    conn.close()
    return dict(event) if event else None

# Отклонение мероприятия (удаление)
async def reject_event(event_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
