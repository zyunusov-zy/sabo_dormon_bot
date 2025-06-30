from aiogram import Router

from . import help
from . import start
from . import register
from . import echo
from . import questionnaire

def register_all_handlers(router: Router):
    router.include_router(start.router)
    router.include_router(register.router)
    router.include_router(questionnaire.router)
