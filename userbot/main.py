import asyncio
import logging
import asyncpg
import argparse
import sys

from bot import GeoSpamBot
from storage import Account, AccountFactory, Person
from settings import BotGlobalSettings


async def main(config_filepath: str = "./settings.toml", log_filepath: str = "userbot.log") -> None:
    log = logging.getLogger("STARTUP")
    log.setLevel(logging.INFO)

    settings = BotGlobalSettings(config_filepath)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    stdhandler = logging.StreamHandler(sys.stdout)
    stdhandler.setLevel(logging.DEBUG)
    stdhandler.setFormatter(formatter)

    filehandler = logging.FileHandler(log_filepath)
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)

    log.addHandler(stdhandler)
    log.addHandler(filehandler)

    log.info(f"Соединение с БД {settings.db_host} {settings.db_name} {settings.db_port} {settings.db_user}")
    try:
        db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
    except Exception as ex:
        log.critical(f"Ошибка подключения к БД: {ex}")
        return None

    Person.set_connection(db_pool)

    AccountFactory.set_connection(db_pool)
    accounts = await AccountFactory.get_accounts()

    log.info("Запуск экземпляров")
    bot_task_list: list = []
    for account in accounts:
        log.info(f"Подготовка {account.session_name}")
        bot = GeoSpamBot(account.session_name, 
                         account.phone_number, 
                         settings.api_id, 
                         settings.api_hash, 
                         settings.control_group_hash,
                         settings.system_version)
        
        bot.log.setLevel(logging.DEBUG)
        bot.log.addHandler(stdhandler)
        bot.log.addHandler(filehandler)

        bot.period_messages_max = settings.period_messages_max
        bot.period_time_s = settings.period_time_s
        
        bot.flood_error_delay_s = settings.flood_error_delay_s

        bot.message_typing_start_delay_min_s = settings.message_typing_start_delay_min_s
        bot.message_typing_start_delay_max_s = settings.message_typing_start_delay_max_s
        bot.message_send_delay_min_s = settings.message_send_delay_min_s
        bot.message_send_delay_max_s = settings.message_send_delay_max_s

        bot.user_spam_delay_min_s = settings.user_spam_delay_min_s
        bot.user_spam_delay_max_s = settings.user_spam_delay_max_s

        bot.skipped_user_spam_delay_min_s = settings.skipped_user_spam_delay_min_s
        bot.skipped_user_spam_delay_max_s = settings.skipped_user_spam_delay_max_s

        bot.geoscan_delay_min_s = settings.geoscan_delay_min_s
        bot.geoscan_delay_max_s = settings.geoscan_delay_max_s

        bot.location_expiration = settings.location_expiration
        
        try:
            await bot.connect()

            bot_task_list.append(
            asyncio.create_task(
                bot.run(account.latitude, 
                        account.longitude,
                        account.delta_latitude,
                        account.delta_longitude,
                        settings.accuracy_radius
                        )
                    )
                )
        except Exception as ex:
            log.error(f"Ошибка запуска {account.session_name}: {ex} {type(ex)}")

    if not bot_task_list:
        log.warning("Зарегистрированные аккаунты отсутствуют.")
        return None
    
    log.info("Запуск экземпляров завершён.")

    await asyncio.wait(bot_task_list)
    return None


async def create_session_files(config_filepath: str = "./settings.toml") -> None:
    settings = BotGlobalSettings(config_filepath)

    if AccountFactory.pool is None:
        try:
            db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
            
            AccountFactory.set_connection(db_pool)
        except Exception as ex:
            print(f"Ошибка подключения к БД: {ex}")
            return None

    accounts = await AccountFactory.get_accounts()

    for account in accounts:
        print(f"Вход в {account.session_name}")
        bot = GeoSpamBot(account.session_name, 
                         account.phone_number, 
                         settings.api_id, 
                         settings.api_hash, 
                         settings.system_version)

        try:
            await bot.connect()
        except Exception as ex:
            print(f"Ошибка запуска {account.session_name}: {ex}")

    return None


async def reg_new_account(config_filepath: str = "./settings.toml", ) -> None:
    print("Режим регистрации нового аккаунта")

    settings = BotGlobalSettings(config_filepath)

    try:
        db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
    except Exception as ex:
        print(f"Ошибка подключения к БД: {ex}")
        return None

    try:
        AccountFactory.set_connection(db_pool)

        account = Account(input("Название сессии (можно указать номер телефона без +): "), 
                          input("Номер телефона: "), 
                          float(input("Широта (разделитель точка): ")), 
                          float(input("Долгота (разделитель точка): ")),
                          float(input("Разброс широты (разделитель точка):")),
                          float(input("Разброс долготы (раделитель точка): ")))
        

        if await AccountFactory.add_account(account):
            print("Новый аккаунт добавлен")
        else:
            print("Такой аккаунт уже существует")

        print("Сейчас мы попытаемся войти во все добавленные аккаунты. \
              Если для каких-то отсутствуют актуальные файлы сессий, \
              введите требуемые данные, чтобы их создать.")
        
        await create_session_files(config_filepath)
    except Exception as ex:
        print(f"Ошибка: {ex}")

    return None


async def remove_account(config_filepath: str = "./settings.toml", ) -> None:
    print("Режим удаления аккаунта")
    print("ИСПОЛЬЗУЙТЕ ТОЛЬКО КОГДА БОТЫ ОСТАНОВЛЕНЫ!")

    settings = BotGlobalSettings(config_filepath)

    

    try:
        db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
    except Exception as ex:
        print(f"Ошибка подключения к БД: {ex}")
        return None

    try:
        AccountFactory.set_connection(db_pool)

        session_name: str = input("Название сессии:")
        phone_number: str = input("Номер телефона:")

        bot = GeoSpamBot(session_name, 
                         phone_number, 
                         settings.api_id, 
                         settings.api_hash, 
                         settings.system_version)

        try:
            await bot.connect()
        except Exception as ex:
            print(f"Ошибка запуска {session_nameк}: {ex}")

        await bot.control_group_leave()

        if await AccountFactory.remove_account(session_name):
            print("Аккаунт удалён")
        else:
            print("Такого аккаунта (сессии) нет")
    except Exception as ex:
        print(f"Ошибка: {ex}")

    return None

async def reset_control_group(config_filepath: str = "./settings.toml", ) -> None:
    print("Режим сброса контрольной группы")

    settings = BotGlobalSettings(config_filepath)

    try:
        db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
    except Exception as ex:
        print(f"Ошибка подключения к БД: {ex}")
        return None

    try:
        AccountFactory.set_connection(db_pool)

        accounts = await AccountFactory.get_accounts()

        for account in accounts:
            print(f"Вход в {account.session_name}")
            bot = GeoSpamBot(account.session_name, 
                            account.phone_number, 
                            settings.api_id, 
                            settings.api_hash, 
                            settings.system_version)

            try:
                await bot.connect()
                await bot.control_group_leave()
            except Exception as ex:
                print(f"Ошибка выхода из группы {account.session_name}: {ex}")

        await AccountFactory.reset_control_group()
        print("Успешно сброшено")

    except Exception as ex:
        print(f"Ошибка сброса: {ex}")

    return None


async def change_location(config_filepath: str = "./settings.toml") -> None:
    print(f"Режим изменения параметров положения")

    session_name = str(input("Имя сессии: "))

    settings = BotGlobalSettings(config_filepath)

    try:
        db_pool = await asyncpg.create_pool(user=settings.db_user, password=settings.db_password,
                                 database=settings.db_name, host=settings.db_host, port=settings.db_port) 
    except Exception as ex:
        print(f"Ошибка подключения к БД: {ex}")
        return None

    try:
        AccountFactory.set_connection(db_pool)

        latitude = float(input("Широта (разделитель точка): "))
        longitude = float(input("Долгота (разделитель точка): "))
        delta_latitude = float(input("Разброс широты (разделитель точка): "))
        delta_longitude = float(input("Разброс долготы (разделитель точка): "))

        if await AccountFactory.change_location(session_name, 
                                                latitude, longitude, 
                                                delta_latitude, delta_longitude):
            print("Параметры позиционирования успешно изменены")
        else:
            print("Такого аккаунта нет")

    except Exception as ex:
        print(f"Ошибка: {ex}")

    return None


def parse_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GeoSpamBot")

    parser.add_argument('--new', 
                        action='store_true',
                    help='Войти в режим регистрации нового аккаунта. Боты запущены не будут.')

    parser.add_argument(
        '--change_location',
        action='store_true',
        help='Войти в режим изменения параметров положения.'
    )

    parser.add_argument(
        '--remove_session',
        action='store_true',
        help='Войти в режим изменения удаления сессии.'
    )

    parser.add_argument(
        '--reset_control_group',
        action='store_true',
        help='Сбросить текущую группу управления и подключиться к новой.'
    )

    parser.add_argument(
        '--config_file',
        default="./settings.toml",
        type=str,
        help='Путь к файлу конфигурации.'
    )

    return parser.parse_args()

if __name__ == "__main__":
    arguments = parse_arguments()

    if arguments.new:
        asyncio.run(reg_new_account(arguments.config_file))
    elif arguments.change_location:
        asyncio.run(change_location(arguments.config_file))
    elif arguments.remove_session:
        asyncio.run(remove_account(arguments.config_file))
    elif arguments.reset_control_group:
        asyncio.run(reset_control_group(arguments.config_file))
    else:
        asyncio.run(main(arguments.config_file))
