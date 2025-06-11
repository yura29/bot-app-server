from aiogram import Router, F
from aiogram.types import Message, WebAppInfo, PreCheckoutQuery, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import httpx

from config_reader import config
from data.festival_schedule import get_current_performance, FESTIVAL_PROGRAM

router = Router()
markup = (
    InlineKeyboardBuilder()
    .button(text="Запустить", web_app=WebAppInfo(url=config.WEBAPP_URL))
).as_markup()

@router.message(CommandStart())
async def start(message: Message) -> None:
    current_time_info = get_current_performance(datetime.now())
    schedule_text = (
        f"📅 Расписание фестиваля:\n"
        f"{current_time_info}\n\n"
        "Если у вас есть вопросы, пишите в любое время, и я отвечу, как только смогу!"
    )
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        f"{schedule_text}",
        reply_markup=markup
    )
    
@router.pre_checkout_query()
async def precheck(event: PreCheckoutQuery) -> None:
    await event.answer(True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    await message.answer("Спасибо за покупку!!!")

@router.message(Command('track'))
async def track_command(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    # Получаем уникальные названия групп из расписания
    group_names = sorted(list(set(event['description'] for event in FESTIVAL_PROGRAM)))
    for i, group_name in enumerate(group_names):
        builder.button(text=group_name, callback_data=f"subscribe_{i}")
    builder.adjust(2) # Размещаем по 2 кнопки в ряд
    await message.answer(
        "Выберите группу для отслеживания:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith('subscribe_'))
async def process_subscribe_callback(callback_query: CallbackQuery) -> None:
    # Получаем уникальные названия групп в том же порядке, что и при создании кнопок
    all_group_names = sorted(list(set(event['description'] for event in FESTIVAL_PROGRAM)))
    
    # Извлекаем индекс из callback_data
    try:
        group_index = int(callback_query.data.split('_', 1)[1])
        group_name = all_group_names[group_index]
    except (ValueError, IndexError):
        await callback_query.answer("Ошибка: Неверные данные для подписки.", show_alert=True)
        return

    user_id = callback_query.from_user.id

    async with httpx.AsyncClient() as client:
        try:
            # Отправляем запрос на наш API для подписки
            response = await client.post(
                f"{config.SERVER_URL}/api/subscribe", # Используем config.SERVER_URL
                json={"group_name": group_name, "user_id": user_id}
            )
            response.raise_for_status() # Вызывает исключение для HTTP ошибок (4xx или 5xx)
            result = response.json()
            message_text = result.get("message", "Неизвестный ответ сервера.")
        except httpx.HTTPStatusError as e:
            message_text = f"Ошибка HTTP при подписке: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            message_text = f"Ошибка запроса при подписке: {e}"
        except Exception as e:
            message_text = f"Непредвиденная ошибка при подписке: {e}"

    await callback_query.answer(message_text, show_alert=True)
    # Отредактировать сообщение с кнопками, чтобы убрать их после выбора
    await callback_query.message.edit_text(
        f"Вы выбрали группу: {group_name}.\n{message_text}",
        reply_markup=None # Убираем клавиатуру
    )