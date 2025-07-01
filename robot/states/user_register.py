from aiogram.fsm.state import State, StatesGroup

class RegisterStates(StatesGroup):
    confirm_honesty = State()
    full_name = State()
    phone_number = State()