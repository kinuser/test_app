Запуск командой ```docker compose up```

Обновление меню реализовано каждые 15 секунд через google sheets API.

Новый тест для эндпоинта лежит в ```tests/tests/test_all_crud.py```.

Для правильной работы тестов, первая синхронизация отложена на 1 минуту.
URL для синхронизации лежит в .env файле. Важно не вставлять атрибуты редактирования,
а вставить согласно примеру (последним должен идти id файла). Id'шники объектов должны быть UUID. Файл вроде как открыт для редактирования, можно поизменять параметры.

Задача для синхронизации реализована в ```src/my_celery```. Синхронизация с учётом скидки. Скидка применяется при просчёте сущностей, в бд хранится цена с уже применённой скидкой.

Не стал удалять некоторые сущности UOF из прошлого этапа (которые идут в разрез с инвалидацией через BackgroundTasks).
При это вся инвалидация выполнена строго через BackgroundTasks.
