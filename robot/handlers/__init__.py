from aiogram import Router
from . import errors
from . import users
from . import groups

def register_all_handlers(router: Router):
    users.register_all_handlers(router)