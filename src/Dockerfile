# 1. используем официальный образ Python
FROM python:3.11-slim

# 2. устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean

# 3. рабочая директория внутри контейнера
WORKDIR /app

# 4. копируем файлы в контейнер
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY .env .

# 5. запускаем скрипт
CMD ["python", "main.py"]
