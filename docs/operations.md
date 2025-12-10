# Операции: деплой, обновления и резервные копии

## Подготовка окружения
1. Скопируйте `.env.example` в `.env` и заполните секреты (БД, Seafile, Telegram, registry, SSH, TLS).
2. Для разработки запускайте `docker compose -f docker-compose.dev.yml up -d --build`.
3. Для продакшена используйте `docker compose -f docker-compose.prod.yml --env-file .env up -d --build` на хосте.

## Бэкапы и откат
- **Снимок БД**: `docker compose -f docker-compose.prod.yml run --rm backup`
  - Скрипт `scripts/backup_postgres.sh` кладёт дампы в `backups/` и удаляет файлы старше `BACKUP_RETENTION_DAYS`.
- **Восстановление**: `docker compose -f docker-compose.prod.yml run --rm backup /scripts/restore_postgres.sh /backups/<dump>.sql` или запустите `scripts/restore_postgres.sh` локально, указав переменные окружения подключения.
- **Версионирование образов**: CI публикует теги `latest` и `sha-<commit>` в `${REGISTRY}/${IMAGE_PREFIX}-<service>`. Для отката выполните `docker compose -f docker-compose.prod.yml pull` нужного тега и `docker compose ... up -d`.

## CI/CD конвейер (GitHub Actions)
1. `lint` + `mypy` + `pytest` для всех Python-сервисов.
2. Сборка образов `api_gateway`, `django`, `intraservice`, `seafile`, `telegram` и пуш в `${REGISTRY}`.
3. Деплой по SSH: `docker compose -f docker-compose.prod.yml pull`, миграции `python manage.py migrate`, затем `up -d --remove-orphans`.
4. Итоговое уведомление отправляется в Telegram чаты из `TELEGRAM_NOTIFY_CHAT_ID`.

## Непрерывное обновление (zero-downtime)
1. **Подготовка**: сделайте бэкап БД и убедитесь, что `docker compose pull` подтянул новые образы.
2. **Миграции**: запустите `docker compose -f docker-compose.prod.yml run --rm django python manage.py migrate` перед перезапуском приложений.
3. **Пошаговая замена**:
   - `docker compose -f docker-compose.prod.yml up -d django` и дождаться `health`/`metrics` (через `curl http://localhost:8000/health/`).
   - Аналогично обновите `api_gateway`, `intraservice`, `seafile`, `telegram` по одному сервису.
4. **Проверка мониторинга**: Prometheus (`:9090`) и Grafana (`:3000`) должны собирать `/metrics` со всех сервисов; убедитесь, что экспортеры (`redis_exporter`, `postgres_exporter`, `celery_exporter`, `node_exporter`, `cadvisor`, `nginx_exporter`) в состоянии `UP`.
5. **Откат**: при проблемах переключитесь на предыдущий тег образа, выполните `docker compose ... up -d` и восстановите БД из последнего дампа при необходимости.

## Контроль состояния
- **Health-checks**: `/health` у nginx, Django, api_gateway, seafile, intraservice; `/health` у Telegram бота на порту `METRICS_PORT`.
- **Метрики**: `/metrics` у всех сервисов; Prometheus собирает также экспортеры БД, Redis, Celery, nginx, host/node и cadvisor.
