from datetime import datetime, time, date

# Расписание фестиваля (дата, время начала и описание)
# Теперь события включают дату, установленную на 28 июня 2025 года, для последующей динамической обработки
FESTIVAL_PROGRAM = [
    {"date": date(2025, 6, 28), "time": "10:00", "description": "Бард-акустическая программа"},
    {"date": date(2025, 6, 28), "time": "12:00", "description": "FROSTSKOLD"},
    {"date": date(2025, 6, 28), "time": "13:00", "description": "SPIRITUS BROTHERS"},
    {"date": date(2025, 6, 28), "time": "14:00", "description": "KINKY DEP"},
    {"date": date(2025, 6, 28), "time": "15:00", "description": "DREAD HAIR"},
    {"date": date(2025, 6, 28), "time": "16:00", "description": "BOOMERANG PROJECT"},
    {"date": date(2025, 6, 28), "time": "17:00", "description": "I.C.WIENER"},
    {"date": date(2025, 6, 28), "time": "18:10", "description": "НЕВСКИЙ ПРОСПЕКТ (трибют гр. «Ленинград»)"},
    {"date": date(2025, 6, 28), "time": "20:10", "description": "IZNUTRI"},
    {"date": date(2025, 6, 28), "time": "21:00", "description": "WHISKY BAR"},
    {"date": date(2025, 6, 28), "time": "22:00", "description": "ОБЫЧНЫЕ ЛЮДИ"},
    {"date": date(2025, 6, 28), "time": "22:40", "description": "DJ CLOUD X"},
]

FESTIVAL_OVER_TEXT = "Фестиваль окончен! Ждём вас в следующем году."

def get_current_performance(current_dt: datetime) -> str:
    """
    Определяет, какое выступление идет в данный момент, или следующее.
    Принимает текущее время (datetime объект).
    """
    current_hour_minute = current_dt.time()
    current_day = current_dt.date()

    next_performance = None
    for i, event in enumerate(FESTIVAL_PROGRAM):
        # Создаем datetime объект для времени события
        event_date_time = datetime.combine(event["date"], time(int(event["time"].split(":")[0]), int(event["time"].split(":")[1])))

        if current_dt < event_date_time:
            # Если текущее время меньше времени начала события, то это следующее событие
            next_performance = event
            break
        elif i + 1 < len(FESTIVAL_PROGRAM):
            next_event = FESTIVAL_PROGRAM[i+1]
            next_event_date_time = datetime.combine(next_event["date"], time(int(next_event["time"].split(":")[0]), int(next_event["time"].split(":")[1])))

            if current_dt >= event_date_time and current_dt < next_event_date_time:
                # Мы находимся внутри текущего события
                return f"Сейчас выступает: {event['description']} (началось {event['date'].strftime('%d.%m')} в {event['time']})"
        else:
            # Если это последнее событие в расписании и его время уже наступило
            if current_dt >= event_date_time:
                return f"Сейчас выступает: {event['description']} (началось {event['date'].strftime('%d.%m')} в {event['time']})"

    if next_performance:
        return f"Следующее выступление: {next_performance['description']} ({next_performance['date'].strftime('%d.%m')}) в {next_performance['time']}"
    else:
        return FESTIVAL_OVER_TEXT

if __name__ == "__main__":
    # Пример использования
    print("--- Текущее время ---")
    print(get_current_performance(datetime(2024, 6, 28, 11, 0))) # 11:00 28 июня
    print(get_current_performance(datetime(2024, 6, 28, 12, 30))) # 12:30 28 июня (после FROSTSKOLD, до SPIRITUS)
    print(get_current_performance(datetime(2024, 6, 28, 22, 50))) # 22:50 28 июня (после DJ CLOUD X)
    print(get_current_performance(datetime(2024, 6, 28, 9, 0))) # 9:00 28 июня
    print(get_current_performance(datetime(2024, 6, 29, 10, 0))) # 10:00 29 июня (другой день) 