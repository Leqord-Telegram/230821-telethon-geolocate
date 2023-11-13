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
                 delta_longitude: float,
                 period_messages: int,
                 control_group_id: int,
                 last_period_timestamp: datetime
                 ):
        self.session_name = session_name
        self.phone_number = phone_number
        self.latitude = latitude
        self.longitude = longitude
        self.delta_latitude = delta_latitude
        self.delta_longitude = delta_longitude
        self.period_messages = period_messages
        self.control_group_id = control_group_id
        self.last_period_timestamp = last_period_timestamp

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
                'SELECT session_name, phone_number, latitude, longitude, delta_latitude, delta_longitude, period_messages, control_group_id, last_period_timestamp FROM sessions',
            )

        account_list = [Account(str(record["session_name"]),
                                str(record["phone_number"]),
                                float(record["latitude"]),
                                float(record["longitude"]),
                                float(record["delta_latitude"]),
                                float(record["delta_longitude"]),
                                int(record["period_messages"]),
                                int(record["control_group_id"]),
                                datetime(record["last_period_timestamp"]),
                                ) for record in records]
        return account_list

    @classmethod
    async def add_account(cls, account: Account) -> bool:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', account.session_name
                )
                exist = values[0]["count"] > 0

                if not exist:
                    await  con.execute('''
                        INSERT INTO sessions(session_name, phone_number, latitude, longitude, delta_latitude, delta_longitude) VALUES($1::text, $2::text, $3::float8, $4::float8, $5::float8, $6::float8)
                    ''', 
                    account.session_name, 
                    account.phone_number, 
                    account.latitude, 
                    account.longitude, 
                    account.delta_latitude, 
                    account.delta_longitude)
            return not exist
    
    @classmethod
    async def remove_account(cls, session_name: str) -> bool:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', session_name
                )
                session_registered = values[0]["count"] > 0

                if session_registered:
                    await  con.execute('''
                        DELETE FROM sessions WHERE session_name=$1::text
                    ''', 
                    session_name)
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

    @classmethod
    async def set_last_period_timestamp(cls, session_name: str, timestamp: datetime | None) -> bool:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', session_name
                )
                session_found = values[0]["count"] > 0

                if session_found:
                    if datetime is None:
                        await  con.execute(f'''
                            UPDATE sessions SET last_period_timestamp = Null WHERE session_name = $1::text
                        ''',  
                        session_name)
                    else:
                        await  con.execute(f'''
                            UPDATE sessions SET last_period_timestamp = $1::timestamp WHERE session_name = $2::text
                        ''',  
                        timestamp, 
                        session_name)
            return session_found
    
    @classmethod
    async def get_last_period_timestamp(cls, session_name: str) -> datetime | None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT last_period_timestamp FROM sessions WHERE session_name=$1::text', session_name
                )

            return values[0]["last_period_timestamp"]
    
    @classmethod
    async def set_period_messages_counter(cls, session_name: str, counter: int | None) -> None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                await  con.execute('''
                        UPDATE sessions SET period_messages = $1::int4 WHERE session_name = $2::text
                    ''',  
                counter, 
                session_name)
            return None
    
    @classmethod
    async def get_period_messages_counter(cls, session_name: str) -> int | None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT period_messages FROM sessions WHERE session_name=$1::text', session_name
                )

            return values[0]["period_messages"]
    
    @classmethod
    async def set_control_group_id(cls, session_name: str, id: int) -> bool:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT COUNT(1) FROM sessions WHERE session_name=$1::text', session_name
                )
                session_found = values[0]["count"] > 0

                if session_found:
                    await  con.execute('''
                        UPDATE sessions SET control_group_id = $1::int8 WHERE session_name = $2::text
                    ''',  
                    id, 
                    session_name)
            return session_found
    
    @classmethod
    async def get_control_group_id(cls, session_name: str) -> int | None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    'SELECT control_group_id FROM sessions WHERE session_name=$1::text', session_name
                )

            return values[0]["control_group_id"]
        
    @classmethod
    async def reset_control_group(cls) -> None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    "UPDATE sessions SET control_group_id = Null"
                )

            return None
        
    @classmethod
    async def clear_spammed_users(cls) -> None:
        async with cls.pool.acquire() as con:
            async with con.transaction():
                values = await con.fetch(
                    "DELETE FROM spammed_users"
                )

            return None
