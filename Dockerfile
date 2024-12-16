# Используем базу изображения с Python и библиотекой aiogram
FROM python:3.9-slim

# Устанавливаем необходимые библиотеки
RUN pip install --upgrade pip
RUN pip install aiogram

# Копируем текущий проект
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Бот будет слушать на порту 8080
CMD ["python", "main.py"]




