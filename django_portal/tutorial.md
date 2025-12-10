# Учебник портала

## Развёртывание
1. Сборка образов: `docker compose -f docker-compose.dev.yml build`.
2. Миграции: `python manage.py migrate` внутри контейнера Django.
3. Создание суперпользователя: `python manage.py createsuperuser`.
4. Сбор статики: `python manage.py collectstatic --noinput`.

## CI/CD
- Рекомендуется запускать `python -m pytest` и `python manage.py test`.
- Добавьте шаги линтинга и проверок миграций в pipeline.

## Бэкапы
- База данных: `pg_dump` по расписанию с сохранением в безопасное хранилище.
- Медиа-файлы: синхронизировать директорию `media/` в S3-совместимое хранилище.

## Примеры расширения
- Добавляйте новые интеграции через модель `IntegrationSettings` и соответствующие ViewSet в `api/views.py`.
- Подключайте вебхуки в `TelegramSettings`, используя Celery-задачи для асинхронной обработки.
