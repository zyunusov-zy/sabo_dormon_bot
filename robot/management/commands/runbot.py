import asyncio
import os
import django
from django.core.management.base import BaseCommand

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties 

from robot.handlers import register_all_handlers
from robot.utils.set_bot_commands import set_default_commands
from robot.utils.notify_admins import on_startup_notify


class Command(BaseCommand):
    help = 'Run the Telegram bot with: python manage.py runbot'

    def handle(self, *args, **options):
        asyncio.run(self.main())

    async def main(self):
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=MemoryStorage())

        register_all_handlers(dp)

        await set_default_commands(bot)
        await on_startup_notify(bot)

        self.stdout.write(self.style.SUCCESS("🚀 Бот запущен"))
        await dp.start_polling(bot)
