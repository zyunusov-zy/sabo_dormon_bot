from aiogram.types import Message


def is_pdf(message: Message) -> bool:
    if message.document:
        return (
            message.document.mime_type == "application/pdf" and
            message.document.file_name.lower().endswith(".pdf")
        )
    return False


def is_image(message: Message) -> bool:
    if message.photo:
        return True
    return False


def is_allowed_file(message: Message) -> bool:
    return is_pdf(message) or is_image(message)
