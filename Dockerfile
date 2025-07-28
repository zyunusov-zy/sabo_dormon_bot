# Используем Python образ
FROM python:3.11

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем pip до той же версии, что у вас в venv
RUN pip install --upgrade pip==25.1.1

# Копируем зависимости и устанавливаем с менее строгой проверкой
COPY requirements.txt .

# Устанавливаем пакеты по одному в правильном порядке, игнорируя конфликты зависимостей
RUN pip install --upgrade pip==25.1.1
RUN pip install --no-deps aiogram3-calendar==0.1.2
RUN pip install -r requirements.txt


COPY . .

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Команда по умолчанию
CMD ["python", "manage.py", "runbot"]