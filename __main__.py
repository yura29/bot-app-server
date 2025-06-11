from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, FastAPI
import uvicorn

from handlers import setup_routers
from api import common

from config_reader import config, dp, bot, lifespan
from aiogram.types import Update

# Инициализация FastAPI здесь
app = FastAPI(lifespan=lifespan) # Инициализируем app здесь

dp.include_router(setup_routers())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(common.router)

# Добавляем эндпоинт для вебхуков Telegram
@app.post(config.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    update = await request.json()
    telegram_update = Update.model_validate(update, context={"bot": bot})
    await dp.feed_update(bot, telegram_update)
    return {"status": "ok"}

# Добавляем временный эндпоинт для проверки здоровья
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT)