# 230821-telethon-geolocate

Это бот, который рассылает сообщения с помощью привязанных аккаунтов telegram.
Рассылка происходит с каждого аккаунта, но так, что дважды одному пользователю сообщения не отправляются.

## Сессия

Каждый аккаунт здесь идентифицируется именем сессии, с которой уже связан номер телефона и прочие данные.
Для каждой сессии создаются файлы ```.session``` и ```.session-journal```, которые нужны для быстрого возобновления работы без повторного входа.
Имена должны быть в латинице без специальных символов и без пробелов.
Если нет необходимости давать разуменые различимые имена сессиям вроде "vasya_near_pushkin",
то рекомендуется называть их номером телефона без "+": например, "79241234567".

## Запуск

Если бот был установлен на сервере Linux вместе с systemd службой, то запустить, остановить, перезапустить и проверить состояние можно следующим образом:

```
sudo systemctl start geospambot   # запустить бота
sudo systemctl stop geospambot    # остановить бота
sudo systemctl restart geospambot # перезапустить бота
sudo systemctl status geospambot  # статус бота
```

## Управление

Рекомендуется выполнить команду ```sudo -i -u telebot-user bash``` и перейти в каталог бота ```cd ~/230821-telethon-geolocate```.

Управлять можно как с помощью готовых скриптов в директории репозитория ```/home/telebot-user/230821-telethon-geolocate```, так и с помощью команд.

Скрипты для управления:
```
./bot_change_location.sh
./bot_clear_users.sh
./bot_new.sh
./bot_remove_session.sh
./bot_reset_control_group.sh
./bot_run.sh
./bot_dry_start.sh
```

Управление также может происходить с помощью команд к main.py.
Предположим, что вы находитесь в директории репозитория 230821-telethon-geolocate.
Сначала следует активировать venv командой 
```source ./venv/bin/activate``` для Linux или ```./venv/Scripts/activate.bat``` для windows.

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

Удалить аккаунт из бота (убрать бота).
```
--remove_session
```

Очистить список пользователей, которым была совершена рассылка.
```
--clear_spammed
```

Очистить ID записанной группы управления. Это необходимо, если вы хотите подключить ботов к новой группе, когда они уже подключены к старой.
```
--reset_control_group
```

## Управляющий канал/группа

Боты последовательно пересылают сообщения из управляющей группы пользователям. Если боты были по той или иной причине отключены от группы,
например, командой ```./bot_reset_control_group.sh```, то они попробуют войти снова в указанную в ```settings.toml``` группу.
Иногда может появляться сообщение вроде ```Устарела ссылка для присоединения к уплавляющему каналу! Пересоздайте и запишите новую в settings.toml``` - это означает, что пригласительная ссылка в группу устарела и боты не могут в нее войти, а ещё это может означать, что в ней опечатка или Телеграм капризничает и тогда нужно создать новую и вписать её символы после знака ```+``` в конфиг ```settings.toml``` в параметр ```group_hash = "asdads"```. Также нужно проверить, нет ли опечаток и избегать ссылок с дефисом ```-``` (перегенерировать, если встретится), потому что при опечатке Telegram всё равно вернет эту ошибку. Если ошибка повторяется, достаточно 2-3 раза попробовать создать новую ссылку и вписать её.


## Параметры

Редактировать параметры можно с помощью команды ```nano <путь к файлу>```. сохранять изменения сочетанием ```Ctrl+O``` и выходить ```Ctrl+X```. Например, если текущая директория - директория бота (выполнена команда ```cd /home/telebot-user/telebot-server/```),
то ```nano ./settings.toml``` откроет конфиг в текущей папке.

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

