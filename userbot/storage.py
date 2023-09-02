import asyncpg
from datetime import datetime


class Person:
    pool: asyncpg.Pool = None

    @classmethod
    def set_connection(cls, pool: asyncpg.Pool) -> None:
        cls.pool = pool
        return None

    @classmethod
    async def add_if_not_exist(cls, id: int, session_name: str) -> None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM spammed_users WHERE id=$1::int8', id
                )
                user_already_spammed = values[0]["count"] > 0

                if not user_already_spammed:
                    await  con.execute('''
                        INSERT INTO spammed_users(id, timestamp, bot_session) VALUES($1::int8, $2::timestamp, $3::text)
                    ''', 
                    id, datetime.now(), session_name)
        return not user_already_spammed
    
class Account:
    def __init__(self, session_name: str, 
                 phone_number: str, 
                 latitude: float, 
                 longitude: float,
                 delta_latitude: float, 
                 delta_longitude: float):
        self.session_name = session_name
        self.phone_number = phone_number
        self.latitude = latitude
        self.longitude = longitude
        self.delta_latitude = delta_latitude
        self.delta_longitude = delta_longitude

class AccountFactory:
    pool: asyncpg.Pool = None

    @classmethod
    def set_connection(cls, pool: asyncpg.Pool) -> None:
        cls.pool = pool
        return None

    @classmethod
    async def get_accounts(cls) -> list:
        async with cls.pool.acquire() as con:
            records = await con.fetch(
                'SELECT session_name, phone_number, latitude, longitude, delta_latitude, delta_longitude FROM sessions',
            )

        account_list = [Account(str(record["session_name"]),
                                str(record["phone_number"]),
                                float(record["latitude"]),
                                float(record["longitude"]),
                                float(record["delta_latitude"]),
                                float(record["delta_longitude"]),
                                ) for record in records]
        return account_list

    @classmethod
    async def add_account(cls, account: Account) -> True:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', account.session_name
                )
                session_registered = values[0]["count"] > 0

                if not session_registered:
                    await  con.execute('''
                        INSERT INTO sessions(session_name, phone_number, latitude, longitude, delta_latitude, delta_longitude) VALUES($1::text, $2::text, $3::float8, $4::float8, $5::float8, $6::float8)
                    ''', 
                    account.session_name, 
                    account.phone_number, 
                    account.latitude, 
                    account.longitude, 
                    account.delta_latitude, 
                    account.delta_longitude)
        return session_registered
    
    @classmethod
    async def change_location(cls, session_name: str, 
                              latitude: float, longitude: float, 
                              delta_latitude: float, delta_longitude: float) -> bool:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', session_name
                )
                session_found = values[0]["count"] > 0

                if session_found:
                    await  con.execute('''
                        UPDATE sessions SET latitude = $1::float8, longitude = $2::float8, delta_latitude = $3::float8, delta_longitude = $4::float8 WHERE session_name = $5::text
                    ''',  
                    latitude, 
                    longitude, 
                    delta_latitude, 
                    delta_longitude,
                    session_name)
        return session_found
