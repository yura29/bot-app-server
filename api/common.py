from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, time # Import datetime and time

from aiogram.types import LabeledPrice, Update
from aiogram.methods import CreateInvoiceLink
from aiogram.utils.web_app import WebAppInitData

from config_reader import config, dp, bot, user_subscriptions
from .utils import auth
from data.festival_schedule import FESTIVAL_PROGRAM

router = APIRouter()

# Новый глобальный для хранения последнего известного user_id
last_known_user_id: Optional[int] = None

class SubscribeRequest(BaseModel):
    group_name: str
    user_id: Optional[int] = None

@router.post("/api/donate", response_class=JSONResponse)
async def donate(request: Request, auth_data: WebAppInitData = Depends(auth)) -> JSONResponse:
    data = await request.json()
    invoice_link = await bot(
        CreateInvoiceLink(
            title="Donate",
            description="Make my life better!",
            payload="donate",
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=data["amount"])]
        )
    )
    
    return JSONResponse({"invoice_link": invoice_link})


@router.post("/api/subscribe", response_class=JSONResponse)
async def subscribe(subscribe_data: SubscribeRequest, auth_data: Optional[WebAppInitData] = Depends(auth)) -> JSONResponse:
    user_id = None
    if auth_data and auth_data.user:
        user_id = auth_data.user.id
    elif last_known_user_id: # Сначала пытаемся использовать last_known_user_id, если WebApp не дал ID
        user_id = last_known_user_id
    elif subscribe_data.user_id: # Только если ни один из выше не сработал, используем заглушку клиента
        user_id = subscribe_data.user_id

    if not user_id:
        return JSONResponse({"status": "error", "message": "Не удалось определить пользователя для подписки."})

    group_name = subscribe_data.group_name

    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = []
    
    if group_name not in user_subscriptions[user_id]:
        user_subscriptions[user_id].append(group_name)
        return JSONResponse({"status": "success", "message": f"Подписка на {group_name} оформлена!"})
    else:
        return JSONResponse({"status": "info", "message": f"Вы уже подписаны на {group_name}."})

@router.get("/api/schedule", response_class=JSONResponse)
async def get_schedule() -> JSONResponse:
    serializable_schedule = []
    for event in FESTIVAL_PROGRAM:
        serializable_event = event.copy()
        serializable_event["date"] = event["date"].isoformat()
        serializable_schedule.append(serializable_event)
            
    return JSONResponse(serializable_schedule)