# Telegram WB Bot — refactor v3

Проект разрезан из монолитного `bot.py` на поддерживаемую структуру.

## Что перенесено

- `app/handlers/start.py` — старт, подписка.
- `app/handlers/lessons.py` — уроки, GetCourse, заявки.
- `app/handlers/unit.py` — юнит-экономика WB, товары, склады, расчёт.
- `app/handlers/admin.py` — статистика, экспорт, рассылки.
- `app/handlers/crm.py` — CRM-панель и команды.
- `app/handlers/media.py` — voice CRM и получение `file_id` видео.
- `app/repositories/*` — слой доступа к SQLite.
- `app/services/*` — WB API, экономика, валидация, безопасность, scheduler, broadcast.
- `alembic/` — миграции.
- `tests/` — базовые тесты экономики и валидации.
- `Dockerfile`, `docker-compose.yml`, `deploy/tgbot.service`, healthcheck.

## Запуск локально

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m app.main
```

## .env

Скопируй `.env.example` в `.env` и подставь реальные значения.

```env
BOT_TOKEN=...
GETCOURSE_URL=...
ADMIN_ID=...
CHANNEL_URL=...
CHANNEL_ID=...
GROQ_API_KEY=...
WB_API_SECRET_KEY=...
DATABASE_PATH=database.db
```

`WB_API_SECRET_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Проверка

```bash
python -m compileall app tests
pytest -q
```

## Миграции

Runtime `init_db()` создаёт таблицы для быстрого запуска. Для продакшена используй Alembic:

```bash
alembic upgrade head
```

## Важное

`unit.py` содержит текстовый catch-all `@router.message(F.text)`, поэтому он подключается последним в `app/main.py`.

## Что нужно сделать дальше

### Unit Economics v2

Текущая юнит-экономика упрощённая.

Нужно реализовать полноценный расчёт отдельно для:

- FBO
- FBS

С поддержкой всех критериев Wildberries:

#### Для FBO:
- комиссия WB
- логистика
- хранение
- приемка
- платная доставка
- индекс локализации
- возвраты
- процент выкупа
- реклама
- участие в акциях
- скидки WB
- налог
- себестоимость
- упаковка
- маржинальность
- ROI
- чистая прибыль

#### Для FBS:
- комиссия WB
- логистика продавца
- последняя миля
- упаковка
- доставка
- возвраты
- процент выкупа
- реклама
- налог
- себестоимость
- операционные расходы
- чистая прибыль
- ROI

### Что должно быть в итоге
Бот должен:
- отдельно считать FBO/FBS
- показывать прибыль на единицу
- показывать чистую маржу
- показывать ROI
- показывать точку безубыточности
- сравнивать FBO vs FBS
- анализировать выгодность модели
- учитывать реальные тарифы WB
- работать через пошаговый wizard интерфейс

### Архитектурные требования
- расчёты вынести в отдельный economics service
- покрыть тестами
- сделать независимые calculators:
  - fbo_calculator.py
  - fbs_calculator.py
- хранить тарифы отдельно
- подготовить переход на PostgreSQL