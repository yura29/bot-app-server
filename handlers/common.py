from aiogram import Router, F
from aiogram.types import Message, WebAppInfo, PreCheckoutQuery, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import httpx

from config_reader import config, user_subscriptions
from data.festival_schedule import get_current_performance, FESTIVAL_PROGRAM, FESTIVAL_OVER_TEXT

router = Router()
markup = (
    InlineKeyboardBuilder()
    .button(text="Запустить", web_app=WebAppInfo(url=config.WEBAPP_URL))
).as_markup()

@router.message(CommandStart())
async def start(message: Message) -> None:
    current_time_info = get_current_performance(datetime.now())
    if current_time_info == FESTIVAL_OVER_TEXT:
        schedule_text = f"{FESTIVAL_OVER_TEXT}\n\nСпасибо, что были с нами! Следите за новостями."
    else:
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

@router.message(Command('stop_tracking'))
async def stop_tracking_command(message: Message) -> None:
    user_id = message.from_user.id
    if user_id in user_subscriptions:
        del user_subscriptions[user_id]
        await message.answer("Все ваши подписки на отслеживание успешно отменены.")
    else:
        await message.answer("У вас нет активных подписок для отслеживания.")

# Новая команда для отписки
@router.message(Command('unsubscribe'))
async def unsubscribe_command(message: Message) -> None:
    user_id = message.from_user.id
    if user_id in user_subscriptions and user_subscriptions[user_id]:
        builder = InlineKeyboardBuilder()
        for i, (group_name, _) in enumerate(user_subscriptions[user_id]):
            builder.button(text=f"Отписаться от {group_name}", callback_data=f"unsubscribe_confirm_{i}")
        builder.adjust(1)
        await message.answer(
            "Выберите группу, от которой хотите отписаться:",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer("Вы еще не подписаны ни на одну группу.")

@router.callback_query(F.data.startswith('unsubscribe_confirm_'))
async def process_unsubscribe_confirm_callback(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    try:
        sub_index = int(callback_query.data.split('_')[-1])
        if user_id in user_subscriptions and len(user_subscriptions[user_id]) > sub_index:
            group_name, _ = user_subscriptions[user_id].pop(sub_index)
            message_text = f"Вы успешно отписались от группы: {group_name}."
            await callback_query.answer(message_text, show_alert=True)
        else:
            message_text = "Ошибка: Подписка не найдена."
            await callback_query.answer(message_text, show_alert=True)
    except (ValueError, IndexError):
        message_text = "Ошибка: Неверные данные для отписки."
        await callback_query.answer(message_text, show_alert=True)
    
    await callback_query.message.edit_text(message_text, reply_markup=None) # Удаляем клавиатуру

@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    await message.answer("Спасибо за покупку!!!")

@router.message(Command('track'))
async def track_command(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    # Получаем уникальные названия групп из расписания
    group_names = sorted(list(set(event['description'] for event in FESTIVAL_PROGRAM)))
    group_name_to_index = {name: i for i, name in enumerate(group_names)} # Создаем маппинг
    for group_name in group_names:
        index = group_name_to_index[group_name]
        builder.button(text=group_name, callback_data=f"select_group_{index}") # Используем индекс
    builder.adjust(2) # Размещаем по 2 кнопки в ряд
    await message.answer(
        "Выберите группу для отслеживания:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith('select_group_'))
async def process_select_group_callback(callback_query: CallbackQuery) -> None:
    # Получаем индекс группы из callback_data
    group_index = int(callback_query.data.split('_')[-1])
    group_names = sorted(list(set(event['description'] for event in FESTIVAL_PROGRAM)))
    
    if group_index >= len(group_names) or group_index < 0:
        await callback_query.answer("Ошибка: Неверные данные группы.", show_alert=True)
        return

    group_name = group_names[group_index] # Получаем название группы по индексу
    user_id = callback_query.from_user.id

    # Проверяем, подписан ли пользователь уже на эту группу
    if user_id in user_subscriptions and any(sub[0] == group_name for sub in user_subscriptions[user_id]):
        message_text = f"Вы уже подписаны на {group_name}. Используйте /unsubscribe для отписки."
        await callback_query.answer(message_text, show_alert=True)
        await callback_query.message.edit_text(message_text, reply_markup=None)
        return

    # Предлагаем выбрать интервал
    interval_options = [10, 15, 20, 25, 30, 60] # Минуты
    builder = InlineKeyboardBuilder()
    for interval in interval_options:
        builder.button(text=f"{interval} мин", callback_data=f"set_interval_{group_index}_{interval}") # Используем индекс
    builder.adjust(3)
    await callback_query.message.edit_text(
        f"Вы выбрали группу: {group_name}. Теперь выберите интервал уведомлений:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith('set_interval_'))
async def process_set_interval_callback(callback_query: CallbackQuery) -> None:
    parts = callback_query.data.split('_')
    group_index = int(parts[2]) # Извлекаем индекс группы
    interval_minutes = int(parts[3])

    group_names = sorted(list(set(event['description'] for event in FESTIVAL_PROGRAM)))
    if group_index >= len(group_names) or group_index < 0:
        await callback_query.answer("Ошибка: Неверные данные группы.", show_alert=True)
        return
    group_name = group_names[group_index] # Получаем название группы по индексу
    user_id = callback_query.from_user.id

    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = []
    
    # Добавляем подписку с интервалом
    user_subscriptions[user_id].append((group_name, interval_minutes))

    message_text = f"Подписка на {group_name} оформлена с уведомлениями каждые {interval_minutes} минут!"
    await callback_query.answer(message_text, show_alert=True)
    await callback_query.message.edit_text(message_text, reply_markup=None) # Убираем клавиатуру