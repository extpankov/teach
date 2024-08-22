# Используем базовый образ Python
FROM python:3.12-slim

# Устанавливаем переменную окружения для отключения буферизации вывода
ENV PYTHONUNBUFFERED=1

# Создаем рабочую директорию в контейнере
WORKDIR /app

# Копируем только requirements.txt перед копированием остального кода
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY . /app

# Указываем команду для запуска приложения
#CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
CMD ["python", "manage.py"]