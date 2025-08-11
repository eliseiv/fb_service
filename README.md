# Facebook Parsing Service

Микросервис для парсинга данных с Facebook с поддержкой различных типов поиска (business, web, google) и интеграцией с RabbitMQ для асинхронной обработки задач.

## 🎯 Основные возможности

- **Многопоточный парсинг** - обработка данных с использованием Selenium и 22 потоков
- **Управление прокси** - автоматическая ротация и проверка прокси-серверов
- **Асинхронная обработка** - интеграция с RabbitMQ для масштабируемости
- **Clean Architecture** - четкое разделение слоев и принципов SOLID
- **Docker поддержка** - готовые контейнеры для быстрого развертывания
- **gRPC API** - высокопроизводительное межсервисное взаимодействие

## 🚀 Быстрый старт

```bash
# Клонирование и запуск с Docker Compose
git clone https://github.com/eliseiv/fb_service.git
cd fb_service
cp env.example .env
docker-compose up -d
```

## 📊 Статистика

- **Типы парсинга**: 3 (Business, Web, Google)
- **Поддерживаемые БД**: PostgreSQL, Redis
- **Брокер сообщений**: RabbitMQ
- **Архитектура**: Clean Architecture + SOLID
- **Контейнеризация**: Docker + Docker Compose

---
