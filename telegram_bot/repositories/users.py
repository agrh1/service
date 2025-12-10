import pathlib
from dataclasses import dataclass
from typing import Optional

import asyncpg

from config import settings


@dataclass
class User:
    telegram_id: int
    username: Optional[str]
    role: str
    is_blocked: bool


class UserRepository:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self.pool:
            return
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
        )
        await self._apply_schema()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def _apply_schema(self) -> None:
        if not self.pool:
            return
        schema_path = pathlib.Path(__file__).with_name("schema.sql")
        sql = schema_path.read_text(encoding="utf-8")
        async with self.pool.acquire() as conn:
            await conn.execute(sql)

    async def get_user(self, telegram_id: int) -> Optional[User]:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT u.telegram_id, u.username, r.name as role, u.is_blocked
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.telegram_id = $1
                """,
                telegram_id,
            )
            if not row:
                return None
            return User(
                telegram_id=row["telegram_id"],
                username=row["username"],
                role=row["role"],
                is_blocked=row["is_blocked"],
            )

    async def register_user(self, telegram_id: int, username: Optional[str], role: str = "user") -> User:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            role_id = await conn.fetchval("SELECT id FROM roles WHERE name = $1", role)
            if role_id is None:
                role_id = await conn.fetchval(
                    "INSERT INTO roles (name) VALUES ($1) RETURNING id", role
                )
            row = await conn.fetchrow(
                """
                INSERT INTO users (telegram_id, username, role_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (telegram_id) DO UPDATE
                SET username = EXCLUDED.username, role_id = EXCLUDED.role_id
                RETURNING telegram_id, username, $4 as role, is_blocked
                """,
                telegram_id,
                username,
                role_id,
                role,
            )
            return User(
                telegram_id=row["telegram_id"],
                username=row["username"],
                role=row["role"],
                is_blocked=row["is_blocked"],
            )

    async def set_role(self, telegram_id: int, role: str) -> Optional[User]:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            role_id = await conn.fetchval("SELECT id FROM roles WHERE name = $1", role)
            if role_id is None:
                role_id = await conn.fetchval(
                    "INSERT INTO roles (name) VALUES ($1) RETURNING id", role
                )
            row = await conn.fetchrow(
                """
                UPDATE users SET role_id = $2
                WHERE telegram_id = $1
                RETURNING telegram_id, username, $3 as role, is_blocked
                """,
                telegram_id,
                role_id,
                role,
            )
            if not row:
                return None
            return User(
                telegram_id=row["telegram_id"],
                username=row["username"],
                role=row["role"],
                is_blocked=row["is_blocked"],
            )

    async def block_user(self, telegram_id: int, blocked: bool = True) -> Optional[User]:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users SET is_blocked = $2
                WHERE telegram_id = $1
                RETURNING telegram_id, username, (SELECT name FROM roles WHERE id = role_id) as role, is_blocked
                """,
                telegram_id,
                blocked,
            )
            if not row:
                return None
            return User(
                telegram_id=row["telegram_id"],
                username=row["username"],
                role=row["role"],
                is_blocked=row["is_blocked"],
            )

    async def set_command_state(self, telegram_id: int, command: str) -> None:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(
                "SELECT id FROM users WHERE telegram_id = $1", telegram_id
            )
            if user_id is None:
                return
            await conn.execute(
                """
                INSERT INTO command_states (user_id, command)
                VALUES ($1, $2)
                ON CONFLICT (user_id, command) DO UPDATE
                SET updated_at = NOW()
                """,
                user_id,
                command,
            )

    async def get_last_command(self, telegram_id: int) -> Optional[str]:
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT command FROM command_states cs
                JOIN users u ON u.id = cs.user_id
                WHERE u.telegram_id = $1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                telegram_id,
            )
            if row:
                return row["command"]
            return None

    async def ensure_user_has_role(self, telegram_id: int, required_roles: list[str]) -> bool:
        user = await self.get_user(telegram_id)
        if not user or user.is_blocked:
            return False
        return user.role in required_roles
