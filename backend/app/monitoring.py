import asyncio
import json
import icmplib
from . import crud
from .database import AsyncSessionLocal
from .manager import manager

async def monitor_devices():
    """
    The main monitoring loop that checks device statuses.
    This function runs as a background task.
    """
    print("INFO:     Monitoring task started.")
    try:
        while True:
            # Створюємо сесію БД всередині циклу, оскільки задача працює поза контекстом запиту
            async with AsyncSessionLocal() as db:
                devices = await crud.get_devices(db)
                for device in devices:
                    if device.is_disabled or not device.ip_address:
                        continue # Пропускаємо вимкнені або пристрої без IP

                    # Пінгуємо пристрій
                    try:
                        host = await icmplib.async_ping(device.ip_address, count=1, timeout=1, privileged=False)
                        is_online_now = host.is_alive
                    except Exception:
                        is_online_now = False

                    # Перевіряємо, чи змінився статус
                    if device.is_online != is_online_now:
                        print(f"INFO:     Status changed for {device.hostname or device.ip_address}: {'ONLINE' if is_online_now else 'OFFLINE'}")
                        # Тут ми будемо оновлювати БД і відправляти повідомлення
                        # Поки що просто відправимо повідомлення
                        update_message = {
                            "type": "status_update",
                            "device_id": device.id,
                            "is_online": is_online_now
                        }
                        await manager.broadcast(json.dumps(update_message))

            # Чекаємо 10 секунд до наступної перевірки
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        # Це виникає, коли ми зупиняємо задачу. Це нормальний вихід.
        print("INFO:     Monitoring task cancelled.")
    except Exception as e:
        # Логуємо інші помилки, але намагаємось продовжити роботу
        print(f"ERROR:    An error occurred in monitoring task: {e}")