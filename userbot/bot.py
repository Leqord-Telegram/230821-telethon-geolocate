import logging
import asyncio
import random

from telethon import TelegramClient, functions, types
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon import errors
from telethon.utils import get_input_peer

from datetime import datetime, timedelta

from storage import Person, AccountFactory
from exceptions import PeriodLimitExceeded

class GeoSpamBot:
    def __init__(self, session_name: str,
                 phone: str,
                 api_id: int, 
                 api_hash: str,
                 control_group_hash: str,
                 system_version: str = "4.16.30-vxTTSGA") -> None:
        
        self.log = logging.getLogger(session_name)
        self.log.setLevel(logging.WARNING)
        
        self.__session_name = session_name
        self.__phone = phone

        self.period_messages_max = None
        self.period_time_s = 24*60*60
        self.__last_period = None
        self.__message_counter = 0
        
        self.flood_error_delay_s = 4*60*60

        self.message_typing_start_delay_min_s = 1
        self.message_typing_start_delay_max_s = 4
        self.message_send_delay_min_s = 3
        self.message_send_delay_max_s = 8

        self.user_spam_delay_min_s = 16
        self.user_spam_delay_max_s = 32

        self.skipped_user_spam_delay_min_s = 4
        self.skipped_user_spam_delay_max_s = 16

        self.geoscan_delay_min_s = 30
        self.geoscan_delay_max_s = 80

        self.location_expiration = None

        self.__api_id = api_id
        self.__api_hash = api_hash

        self.__control_group_id = None
        self.__control_group_hash = control_group_hash

        self.system_version = system_version

    async def connect(self):
        self.log.info(f"Запуск экземпляра")
        self.__client = TelegramClient(self.__session_name, 
                                       self.__api_id, 
                                       self.__api_hash, 
                                       system_version=self.system_version)
        await self.__client.start(phone=self.__phone)
        self.log.info(f"Экземпляр запущен")

    async def __control_group_check_join(self) -> bool:
        await self.__client.connect()

        control_group_id = await AccountFactory.get_control_group_id(self.__session_name)

        if control_group_id is None:
            try:
                updates = await self.__client(ImportChatInviteRequest(self.__control_group_hash))
                self.log.info(f"Успешно подключен к группе управления.")
                self.__control_group_id = updates.chats[0].id
                await AccountFactory.set_control_group_id(self.__session_name, self.__control_group_id)
            except errors.rpcerrorlist.UserAlreadyParticipantError:
                raise Exception("Бот уже состоит в контрольной группе, но её id не записан. Если вы сами добавили его туда, удалите и повторите снова.")
        else:
            self.log.info(f"Уже состоит в группе управления.")
            self.__control_group_id = await AccountFactory.get_control_group_id(self.__session_name)
        return True
    
    async def __update_last_period(self) -> None:
        await AccountFactory.set_last_period_timestamp(self.__session_name, datetime.now())
        return None

    async def __set_message_counter(self, counter: int) -> None:
        await AccountFactory.set_period_messages_counter(self.__session_name, counter)
        self.__message_counter = counter
        return None

    
    async def __initial_period_sleep_check(self) -> bool:
        if self.period_messages_max is None:
            self.log.info("Лимит сообщений за определенный период отключён.")
            return False
        else:
            self.log.info(f"Лимит сообщений {self.period_messages_max} за период {self.period_time_s} активен.")

            self.__message_counter = await AccountFactory.get_period_messages_counter(self.__session_name)

            if self.__message_counter is None:
                self.__set_message_counter(0)
                self.log.info(f"Счётчик сообщений не задан и установлен в 0.")
            else:
                self.log.info(f"Уже было отправлено {self.__message_counter} сообщений")

            self.__last_period = await AccountFactory.get_last_period_timestamp(self.__session_name)

            if self.__last_period is not None:
                await self.__max_messages_per_period_check()
            else:
                await self.__update_last_period()
            
            return True

    async def __max_messages_per_period_check(self) -> bool:
        if self.period_messages_max is not None:
            if (datetime.now() - self.__last_period) > timedelta(seconds=self.period_time_s):
                self.log.info("Период уже закончен, сбрасываю счётчик сообщений.")

                await self.__update_last_period()
                await self.__set_message_counter(0)
                
            if self.__message_counter >= self.period_messages_max:
                if (datetime.now() - self.__last_period) < timedelta(seconds=self.period_time_s):
                        sleep_until: datetime = self.__last_period + timedelta(seconds=self.period_time_s)
                        sleep_delta: timedelta = sleep_until - datetime.now()

                        self.log.info(f"Лимит сообщений превышен. Засыпаю до {sleep_until} на {sleep_delta}.")

                        await self.__client.disconnect()
                        await asyncio.sleep(sleep_delta.total_seconds())
                        await self.__client.connect()
                        
                        await self.__update_last_period()
                        await self.__set_message_counter(0)
                        self.log.info(f"Возобновляю работу. Счётчик сброшен.")
            else:
                await self.__set_message_counter(self.__message_counter + 1)
            return True
        return False

    async def run(self, latitude: float, longitude: float, delta_latitude: float, delta_longitude: float, accuracy_radius: int) -> None:  
        self.log.info(f"Запуск задачи. Базовая широта: {latitude} Базовая долгота: {longitude} Разброс широты: {delta_latitude} Разброс долготы: {delta_longitude} Радиус точности: {accuracy_radius}")
        try:
            await self.__client.connect()
            await self.__control_group_check_join()
            await self.__initial_period_sleep_check()

            while True:
                try:
                    self.log.debug(f"Запуск итерации сканирования и рассылки")
                    current_latitude = latitude
                    current_longitude = longitude

                    if delta_latitude > 0:
                        current_latitude += random.uniform(-1.*delta_latitude, delta_latitude)
                    if delta_longitude > 0:
                        current_longitude += random.uniform(-1.*delta_longitude, delta_longitude)

                    self.log.debug(f"Сканирование. Широта: {current_latitude} Долгота: {current_longitude}")
                    await self.__spam_people_nearby(current_latitude, current_longitude, accuracy_radius)

                except (errors.rpcerrorlist.PeerFloodError, errors.rpcerrorlist.FloodWaitError) as ex:
                    self.log.warning(f"Получена блокировка флуда. Ухожу в режим ожидания.")

                    await self.__client.disconnect()
                    await asyncio.sleep(self.flood_error_delay_s)
                    await self.__client.connect()

                    self.log.info(f"Работа возобновлена.")
        except Exception as ex:
                    self.log.critical(ex, exc_info=True)
        finally:
            self.log.info("Заверщение соединения перед завершением работы")
            if self.__client.is_connected():
                await self.__client.disconnect()

        return None


    async def __spam_people_nearby(self, latitude: float, longitude: float, accuracy_radius: int) -> None:
        point = await self.__client(functions.contacts.GetLocatedRequest(
                geo_point=types.InputGeoPoint(lat=latitude, long=longitude, accuracy_radius=accuracy_radius),
                self_expires=self.location_expiration,
            )
        )

        self.log.debug(f"Получено обновлений: {len(point.updates)}")
        for update_peer_located in point.updates:
            self.log.debug(f"Получено пользователей: {len(update_peer_located.peers)}")
            for peer_located in update_peer_located.peers:
                try:
                    if not isinstance(peer_located.peer, types.PeerUser):
                        self.log.debug(f"Пропускаем пир типа {type(peer_located.peer)}")
                        continue

                    person = await self.__client(GetFullUserRequest(peer_located.peer.user_id))

                    self.log.debug(f"Аккаунт получен: id {person.full_user.id} дистанция {peer_located.distance}")

                    #sent_succesfully = await self.__send_to_user(person.full_user.id)
                    sent_succesfully = await self.__send_to_user(885023520)
                    # TODO: вернуть

                    if sent_succesfully:
                        await asyncio.sleep(
                            random.randint(self.user_spam_delay_min_s, self.user_spam_delay_max_s)
                        )
                    else:
                        await asyncio.sleep(
                            random.randint(self.skipped_user_spam_delay_min_s, self.skipped_user_spam_delay_max_s)
                        )
                except AttributeError as ex:
                    self.log.error(f"Ошибка получения ближайших аккаунтов: {ex}")
                except errors.rpcerrorlist.UserPrivacyRestrictedError as ex:
                    self.log.warning(ex, exc_info=True)
                except errors.rpcerrorlist.InputUserDeactivatedError as ex:
                    self.log.warning(ex, exc_info=True)
    
    async def __send_to_user(self, id: int) -> bool:
        #if not await Person.add_if_not_exist(id, self.__session_name):
        #    self.log.debug(f"Уже разослано: {id}")
        #    return False
        # TODO: вернуть
        
        await self.__max_messages_per_period_check()

        self.log.debug(f"Отправляем рассылку пользователю {id}")
        async for message in reversed(self.__client.iter_messages(await self.__client.get_entity(self.__control_group_id))):
            if not isinstance(message, types.MessageService):
                await asyncio.sleep(
                    random.randint(
                    self.message_typing_start_delay_min_s, 
                    self.message_typing_start_delay_max_s
                    ))
                
                input_peer = get_input_peer(await self.__client.get_entity(id))

                await self.__client(
                    functions.messages.SetTypingRequest(
                    peer=input_peer,
                    action=types.SendMessageTypingAction()
                    ))
                
                await asyncio.sleep(
                    random.randint(
                    self.message_send_delay_min_s, 
                    self.message_send_delay_max_s
                    ))

                await self.__client.send_message(input_peer, message)

                await self.__client(
                    functions.messages.SetTypingRequest(
                    peer=input_peer,
                    action=types.SendMessageCancelAction()
                    ))
        
        return True
