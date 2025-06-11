from os.path import join, dirname
from typing import AsyncGenerator
import asyncio
from datetime import datetime, time, date, timedelta

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from fastapi import FastAPI

from data.festival_schedule import FESTIVAL_PROGRAM

# Временное хранилище для подписок: {user_id: [group_name1, group_name2, ...]}
user_subscriptions: dict[int, list[str]] = {}

class Config(BaseSettings):
    BOT_TOKEN: SecretStr
    
    WEBAPP_URL: str = "https://you-festival-web.vercel.app" #client
    WEBHOOK_URL: str = "https://you-festival-web.onrender.com" #server
    WEBHOOK_PATH: str = "/webhook"
    
    APP_HOST: str = "localhost"
    APP_PORT: int = 8000
    
    @property
    def SERVER_URL(self) -> str:
        return f"http://{self.APP_HOST}:{self.APP_PORT}"

    model_config = SettingsConfigDict(
        env_file=join(dirname(__file__), ".env"),
        env_file_encoding="utf-8"
    )

# Глобальное хранилище для отслеживания отправленных уведомлений
sent_notifications = set() # (user_id, group_name, hour, minute) for each sent notification

async def notification_scheduler():
    while True:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        for user_id, subscribed_groups in user_subscriptions.items():
            for group_name in subscribed_groups:
                # Ищем событие, на которое подписан пользователь
                event = next((e for e in FESTIVAL_PROGRAM if e["description"] == group_name), None)
                
                if event:
                    event_datetime = datetime.combine(event["date"], time(int(event["time"].split(":")[0]), int(event["time"].split(":")[1])))
                    
                    # Убедимся, что событие еще не прошло
                    if now < event_datetime or (now.date() == event_datetime.date() and now.time() < event_datetime.time()):
                        # Создаем уникальный идентификатор для уведомления в эту минуту
                        notification_id = (user_id, group_name, current_hour, current_minute)

                        if notification_id not in sent_notifications:
                            message = f"Бот: Статус для \"{group_name}\": Следующее выступление {event['date'].strftime('%d.%m')} в {event['time']}. (Тестовое сообщение) "
                            try:
                                await bot.send_message(chat_id=user_id, text=message)
                                sent_notifications.add(notification_id)
                            except Exception as e:
                                pass # print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}") # Закомментировано для удаления логов
        
        await asyncio.sleep(60) # Проверяем расписание каждую минуту (возвращено с 1 секунды)


async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Запускаем фоновую задачу уведомлений
    task = asyncio.create_task(notification_scheduler())

    await bot.set_webhook(
        url=f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}",
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types()
    )

    # Определяем список команд
    commands = [
        BotCommand(command="start", description="Запустить бота и получить расписание"),
        BotCommand(command="track", description="Отслеживать группу"),
    ]
    # Устанавливаем команды для бота
    await bot.set_my_commands(commands)
    
    yield
    # Отменяем фоновую задачу при завершении работы приложения
    task.cancel()
    try:
        await task  # Ждем отмены задачи
    except asyncio.CancelledError:
        pass
    await bot.session.close()


config = Config()

bot = Bot(config.BOT_TOKEN.get_secret_value())
dp = Dispatcher()
app = FastAPI(lifespan=lifespan) # Удален port=443, Render управляет портами через Uvicorn
