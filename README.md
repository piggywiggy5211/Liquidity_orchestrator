# Liquidity Orchestrator

Проект для оркестрации ликвидности (Onramp/Offramp).

## Установка зависимостей

Проект использует `uv` для управления зависимостями.
```bash
uv sync
```

## Работа с базой данных (Alembic)
Миграции находятся в папке `app/database/alembic`.

### Запуск миграций
Для применения всех миграций к базе данных:
```bash
uv run alembic upgrade head
```

### Создание новой миграции
Для автоматической генерации миграции на основе изменений в моделях SQLAlchemy:
```bash
uv run alembic revision --autogenerate -m "ваше описание"
```

## Тестирование
### Запуск всех тестов
```bash
uv run pytest -vv
```


## Запуск приложения

```bash
uv run uvicorn main:app --reload
```
