import psycopg
import validators
from typing import Optional
from .user import User


class UsersService:
    def __init__(self, aconn: psycopg.AsyncConnection):
        self._aconn = aconn
        self._users_table = "users"

    async def register_user(self, username: str, email: str, password: str) -> User:
        self._validate_password(password=password)

        await self._validate_username(username=username)

        await self._validate_email(email=email)

        async with self._aconn.cursor() as acur:
            insert_user_query = f"""
                INSERT INTO {self._users_table} (username, email, password_hash) 
                VALUES (%s, %s, crypt(%s, gen_salt('bf')))
                RETURNING id; 
            """

            await acur.execute(insert_user_query, (username, email, password))

            record = await acur.fetchone()

            user = User(
                _id=record[0],
                username=username,
                email=email,
                bio=None,
                image=None,
            )

            return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with self._aconn.cursor() as acur:
            get_user_by_username_query = f"""
                        SELECT id, email, bio, image
                        FROM {self._users_table}
                        WHERE username = %s;
                    """

            await acur.execute(get_user_by_username_query, (username,))

            record = await acur.fetchone()

            if not record:
                return

            user = User(
                _id=record[0],
                username=username,
                email=record[1],
                bio=record[2],
                image=record[3],
            )

            return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self._aconn.cursor() as acur:
            get_user_by_email_query = f"""
                        SELECT id, username, bio, image
                        FROM {self._users_table}
                        WHERE email = %s;
                    """

            await acur.execute(get_user_by_email_query, (email,))

            record = await acur.fetchone()

            if not record:
                return

            user = User(
                _id=record[0],
                username=record[1],
                email=email,
                bio=record[2],
                image=record[3],
            )

            return user

    async def _validate_username(self, username: str):
        existing_user = await self.get_user_by_username(username=username)

        if existing_user:
            raise ValueError(f"username is taken")

    async def _validate_email(self, email: str):
        if not validators.email(email):
            raise ValueError(f"invalid email {email}")

        existing_user = await self.get_user_by_email(email=email)

        if existing_user:
            raise ValueError(f"email is taken")

    @staticmethod
    def _validate_password(password: str):
        min_password_length = 8
        max_password_length = 64

        if not len(password) >= min_password_length:
            raise ValueError(
                f"password length must be greater than or equal to {min_password_length}"
            )

        if not len(password) <= max_password_length:
            raise ValueError(
                f"password length must be less than or equal to {max_password_length}"
            )
