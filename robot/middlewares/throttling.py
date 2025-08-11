import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any
import time


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 2.0):
        self.rate_limit = rate_limit
        self._last_called: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Any],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = message.from_user.id
        now = time.time()

        last_time = self._last_called.get(user_id, 0)
        delta = now - last_time

        if delta < self.rate_limit:
            await message.answer("⏱ Пожалуйста, не так быстро. Подождите немного...")
            return

        self._last_called[user_id] = now
        return await handler(message, data)
