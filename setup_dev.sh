#!/bin/bash

# ============================================================
# СКРИПТ ИНИЦИАЛИЗАЦИИ ОКРУЖЕНИЯ РАЗРАБОТКИ
# ============================================================

set -e

echo "🚀 Инициализация окружения разработки..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================
# 1. ПРОВЕРКА ТРЕБОВАНИЙ
# ============================================================

echo -e "${YELLOW}📋 Проверка требований...${NC}"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    echo "Установите Docker с https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker найден${NC}"

# Проверка docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose не установлен!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ docker-compose найден${NC}"

# ============================================================
# 2. СОЗДАНИЕ .env ФАЙЛА
# ============================================================

echo -e "${YELLOW}📝 Настройка переменных окружения...${NC}"

if [ ! -f .env ]; then
    echo "Создание .env из .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env создан${NC}"
    echo "Отредактируйте .env если нужны специальные настройки"
else
    echo -e "${GREEN}✅ .env уже существует${NC}"
fi

# ============================================================
# 3. СОЗДАНИЕ СТРУКТУРЫ МИКРОСЕРВИСОВ
# ============================================================

echo -e "${YELLOW}📁 Создание структуры проекта...${NC}"

# Директории микросервисов
SERVICES=(
    "config_portal"
    "intraservice_service"
    "seafile_service"
    "telegram_service"
)

for service in "${SERVICES[@]}"; do
    if [ ! -d "$service" ]; then
        echo "Создание директории $service..."
        mkdir -p "$service"
        touch "$service/.gitkeep"
    fi
done

echo -e "${GREEN}✅ Структура проекта создана${NC}"

# ============================================================
# 4. ПРОВЕРКА ПОРТОВ
# ============================================================

echo -e "${YELLOW}🔍 Проверка доступности портов...${NC}"

PORTS=(5432 6379 8000 8001 8002 8003)
OCCUPIED_PORTS=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        OCCUPIED_PORTS+=($port)
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Внимание: Следующие порты уже используются:${NC}"
    printf '%s\n' "${OCCUPIED_PORTS[@]}"
    echo "Убедитесь что других контейнеров нет запущено"
fi

echo -e "${GREEN}✅ Проверка портов завершена${NC}"

# ============================================================
# 5. ИНФОРМАЦИЯ О СЛЕДУЮЩИХ ШАГАХ
# ============================================================

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Инициализация завершена!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo "📚 Следующие шаги:"
echo ""
echo "1️⃣  Запустите контейнеры:"
echo "   docker-compose f docker-compose.dev.yml up -d"
echo ""
echo "2️⃣  Проверьте статус:"
echo "   docker-compose -f docker-compose.dev.yml ps"
echo ""
echo "3️⃣  Посмотрите логи:"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "4️⃣  Проверьте health check:"
echo "   curl http://localhost:8000/health/"
echo ""
echo -e "${YELLOW}💡 Совет:${NC} Каждый микросервис требует Dockerfile"
echo "Посмотрите SPRINT_1_DJANGO_PORTAL.md для первого сервиса"
echo ""
