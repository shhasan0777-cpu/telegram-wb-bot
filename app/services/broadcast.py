import asyncio, logging
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest

log=logging.getLogger(__name__)

async def safe_send_message(bot: Bot, user_id: int, text: str, reply_markup=None) -> bool:
    try:
        await bot.send_message(user_id, text, reply_markup=reply_markup)
        await asyncio.sleep(0.05)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after + 1)
        try:
            await bot.send_message(user_id, text, reply_markup=reply_markup)
            return True
        except Exception:
            log.exception("Retry send failed")
            return False
    except (TelegramForbiddenError, TelegramBadRequest):
        return False
    except Exception:
        log.exception("Broadcast send failed")
        return False
