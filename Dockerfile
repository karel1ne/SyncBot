FROM python:3.12-slim

# Установка переменных окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Обновляем пакеты и устанавливаем инструменты сборки (gcc)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости системы (в глобальное окружение)
RUN uv sync --no-dev

# Копируем исходный код
COPY . .

# Команда для запуска
CMD ["uv", "run", "python", "-m", "syncbot"]