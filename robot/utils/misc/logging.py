import logging
import os
from datetime import datetime
import sys

os.makedirs("logs", exist_ok=True)

class DetailedFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'user_id'):
            record.user_info = f"[USER:{record.user_id}]"
        else:
            record.user_info = ""
            
        if hasattr(record, 'state'):
            record.state_info = f"[STATE:{record.state}]"
        else:
            record.state_info = ""
            
        return super().format(record)

formatter = DetailedFormatter(
    fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(user_info)s %(state_info)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("sabo_bot")
logger.setLevel(logging.DEBUG)
logger.propagate = False # удалить чтобы вывести в терминал
logger.handlers.clear()

file_handler = logging.FileHandler(
    f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log", 
    mode="a", 
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

error_handler = logging.FileHandler(
    f"logs/errors_{datetime.now().strftime('%Y%m%d')}.log", 
    mode="a", 
    encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setLevel(logging.INFO)
# console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(error_handler)
# logger.addHandler(console_handler)

def log_user_action(user_id, action, state=None, extra_data=None):
    """Логирование действий пользователя"""
    extra = {'user_id': user_id}
    if state:
        extra['state'] = state
    
    msg = f"User action: {action}"
    if extra_data:
        msg += f" | Data: {extra_data}"
    
    logger.info(msg, extra=extra)

def log_state_change(user_id, old_state, new_state):
    """Логирование изменения состояния"""
    extra = {'user_id': user_id, 'state': f"{old_state}->{new_state}"}
    logger.info(f"State changed: {old_state} -> {new_state}", extra=extra)

def log_error(user_id, error, context=None, state=None):
    """Логирование ошибок"""
    extra = {'user_id': user_id}
    if state:
        extra['state'] = state
    
    msg = f"Error occurred: {str(error)}"
    if context:
        msg += f" | Context: {context}"
    
    logger.error(msg, extra=extra, exc_info=True)

def log_file_operation(user_id, operation, file_info, success=True):
    """Логирование файловых операций"""
    extra = {'user_id': user_id}
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"File operation {status}: {operation} | {file_info}", extra=extra)

def log_handler(func):
    """Декоратор для логирования всех хендлеров"""
    import functools
    import inspect

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        message = None
        state = None

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for param_name, param_value in bound_args.arguments.items():
            if hasattr(param_value, 'from_user') and hasattr(param_value, 'chat'):
                message = param_value
            elif hasattr(param_value, 'get_state'):
                state = param_value

        user_id = message.from_user.id if message and hasattr(message, 'from_user') else 'unknown'
        current_state = await state.get_state() if state else None

        text_value = getattr(message, 'text', None)
        if text_value is None:
            extra = f"Content type: {getattr(message, 'content_type', 'unknown')}"
        else:
            extra = f"Text: {text_value[:50]}"

        log_user_action(
            user_id=user_id,
            action=f"Handler: {func.__name__}",
            state=current_state,
            extra_data=extra
        )

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            log_error(
                user_id=user_id,
                error=e,
                context=f"Handler: {func.__name__}",
                state=current_state
            )
            raise

    return wrapper
