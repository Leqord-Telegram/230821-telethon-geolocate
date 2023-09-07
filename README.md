# 230821-telethon-geolocate

Это бот, который рассылает сообщения с помощью привязанных аккаунтов telegram.
Рассылка происходит с каждого аккаунта, но так, что дважды одному пользователю сообщения не отправляются.

## Сессия

Каждый аккаунт здесь идентифицируется именем сессии, с которой уже связан номер телефона и прочие данные.
Имена должны быть в латинице без специальных символов и без пробелов.
Если нет необходимости давать разуменые различимые имена сессиям вроде "vasya_near_pushkin",
то рекомендуется называть их номером телефона без "+": например, "79241234567".

## Запуск

Если бот был установлен на сервере Linux вместе с systemd службой, то запустить, остановить, перезапустить и проверить состояние можно следующим образом:

```
systemctl start geospambot
systemctl stop geospambot
systemctl restart geospambot
systemctl status geospambot
```

## Управление

Управление происходит с помощью команд к main.py.
Предположим, что вы находитесь в директории репозитория 230821-telethon-geolocate.
Сначала следует активировать venv командой source ./venv/bin/activate для Linux или ./venv/Scripts/activate.bat для windows.

Затем можно выполнять команды:
```
python3 ./userbot/main.py <команда>
```
Если команду не передать, боты будут запущены.

Существуют следующие команды:

Режим изменения местоположения бота.
```
--change_location
```

Удалить аккаунт.
```
--remove_session
```

Очистить ID записанной группы управления. Это необходимо, если вы хотите подключить ботов к новой группе, когда они уже подключены к старой.
```
--reset_control_group
```

## Параметры

В каталоге есть шаблонный файл "settings_template.toml", его следует скопировать и переименовать в "settings.toml" и вписать туда актуальные данные входа. Скорее всего, после первой настройки он уже будет и удалять его не нужно.

Рассмотрим параметры, который он содержит.

Следующие параметры служат для входа в аккаунт и не должны меняться после первой настройки.
```
api_id = 12345
api_hash = "12345"
db_user = "telebot_user"
db_password = "12345"
```

Этот параметр содержит символы в строке-приглашении в управляющую группу после знака "+".
После изменения этого параметра нужно запустить соответствующий скрипт.
```
group_hash = "asdads"
```

Эти параметры настраивают ограничения и задержки работы бота.

Этот параметр устанавливает максимальное количество сообщений за некоторый период. Его можно удалить и тогда лимит будет снят, но это может вызвать бан аккаунта.
```
period_messages_max = 30
```

Если предыдущий парамтр устуказан, то также должен быть указан и этот - длина периода ограничения в секундах.
Когда количество отправленных сообщений за этот период будет превышено, бот заснет до его окончания.
```
period_time_s = 80000
```

Время засыпания после получения бана за флуд в секундах.
```
flood_error_delay_s = 20000
```

Минимальная и максимальная задержка от последнего отправленного сообщения до начачала "печатания" ботом.
```
message_typing_start_delay_min_s = 1
message_typing_start_delay_max_s = 4
```

Минимальная и максимальная задержка перед отправкой сообщения после начала "печатания".
```
message_send_delay_min_s = 2
message_send_delay_max_s = 8
```

Минимальная и максимальная задержка между рассылкой разным пользователям.
```
user_spam_delay_min_s = 60
user_spam_delay_max_s = 180
```

Минимальная и максимальная задержка после пользователя, которому уже были разосланы сообщения.
```
skipped_user_spam_delay_min_s = 1
skipped_user_spam_delay_max_s = 3
```

Минимальная и максимальная задержка между сканированием пользователей вокруг.
```
geoscan_delay_min_s = 60
geoscan_delay_max_s = 180
```

Этот параметр отвечает за передаваемую Telegram погрешность местоположения, его не следует менять.
```
accuracy_radius=500
```

Эти параметры отвечают за подключение к БД и их не следует менять после первой настройки.
```
db_name = "telebot"
db_host = "localhost"
db_port = 5432
```

