import logging
import asyncio
import random

from telethon import TelegramClient, functions, types
from telethon.tl.functions.users import GetFullUserRequest
from telethon import errors
from telethon.utils import get_input_peer

from storage import Person
from exceptions import PeriodLimitExceeded

class GeoSpamBot:
    def __init__(self, session_name: str,
                 phone: str,
                 api_id: int, 
                 api_hash: str,
                 system_version: str = "4.16.30-vxTTSGA") -> None:
        
        self.log = logging.getLogger(session_name)
        self.log.setLevel(logging.WARNING)
        
        self.__session_name = session_name
        self.__phone = phone

        self.period_messages_max = None
        self.period_time_s = 24*60*60
        self.messages_sent = 0
        
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
        self.system_version = system_version

    async def connect(self):
        self.log.info(f"Запуск экземпляра")
        self.__client = TelegramClient(self.__session_name, 
                                       self.__api_id, 
                                       self.__api_hash, 
                                       system_version=self.system_version)
        await self.__client.start(phone=self.__phone)
        self.log.info(f"Экземпляр запущен")

    async def run(self, latitude: float, longitude: float, delta_latitude: float, delta_longitude: float, accuracy_radius: int) -> None:  
        self.log.info(f"Запуск задачи. Базовая широта: {latitude} Базовая долгота: {longitude} Разброс широты: {delta_latitude} Разброс долготы: {delta_longitude} Радиус точности: {accuracy_radius}")
        try:
            await self.__client.connect()
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
                except PeriodLimitExceeded as ex:
                    self.log.info("Превышен лимит рассылок. Счётчик очищен. Засыпаю.")
                    self.messages_sent = 0
                    await asyncio.sleep(self.period_time_s)
                    self.log.info("Ожидание закончено. Дневной лимит сброшен. Возобновляю работу.")
                    continue
                except errors.rpcerrorlist.PeerFloodError as ex:
                    self.log.warning(f"Получена блокировка флуда. Ухожу в режим ожидания.")

                    await self.__client.disconnect()
                    await asyncio.sleep(self.flood_error_delay_s)
                    await self.__client.connect()

                    self.log.info(f"Работа возобновлена.")
                except Exception as ex:
                    self.log.critical(ex, exc_info=True)
        finally:
            # TODO: убрать
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

                    sent_succesfully = await self.__send_to_user(person.full_user.id)

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
        if not await Person.add_if_not_exist(id, self.__session_name):
            self.log.debug(f"Уже разослано: {id}")
            return False
        
        if self.period_messages_max is not None:
            if self.messages_sent > self.period_messages_max:
                self.log.debug(f"Рассылка не отправлена пользователю {id} - превышен лимит рассылок в день {self.period_messages_max}")
                raise PeriodLimitExceeded(f"Превышен лимит рассылок в день {self.period_messages_max}")
            self.messages_sent += 1

        self.log.debug(f"Отправляем рассылку пользователю {id}")
        async for message in reversed(self.__client.iter_messages('me')):
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
