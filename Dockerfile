FROM python:3.13-slim

# Установка переменных окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости системы (в глобальное окружение)
RUN uv sync --no-dev --system

# Копируем исходный код
COPY . .

# Команда для запуска
CMD ["syncbot"]