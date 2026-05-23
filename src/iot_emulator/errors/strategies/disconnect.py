import asyncio
import logging
from typing import Optional, Callable
import random



logger = logging.getLogger(__name__)

# Стратегия отключения устройства. Эмулирует временную потерю связи.
class DisconnectStrategy:

    def __init__(self, duration: float = 5.0, rate: float = 0.01):
        self.duration = duration   # Длительность отключения в секундах
        self.rate = rate           # Вероятность отключения за одну публикацию
        self._is_disconnected = False   # False - устройство работает нормально, True - устройство отключено
        self._disconnect_callback: Optional[Callable] = None
        self._reconnect_callback: Optional[Callable] = None

    # Установить callback для отключения/подключения
    def set_callbacks(self, on_disconnect: Callable, on_reconnect: Callable) -> None:
        self._disconnect_callback = on_disconnect
        self._reconnect_callback = on_reconnect

    # Проверить, нужно ли отключиться/подключиться.
    async def check_and_apply(self) -> bool:
        if not self._is_disconnected:                         # Проверяем, нужно ли отключиться
            if random.random() < self.rate:
                self._is_disconnected = True
                logger.warning(f"Disconnect strategy: disconnecting for {self.duration}s")
                if self._disconnect_callback:
                    await self._disconnect_callback()
                # Запускаем таймер на подключение
                asyncio.create_task(self._reconnect_after_delay())
                return True
        return self._is_disconnected

    # Подключиться после задержки
    async def _reconnect_after_delay(self) -> None:
        await asyncio.sleep(self.duration)
        self._is_disconnected = False
        logger.info("Disconnect strategy: reconnected")
        if self._reconnect_callback:
            await self._reconnect_callback()

    # Обновить параметры отключения
    def update_params(self, duration: float = None, rate: float = None) -> None:
        if duration is not None:
            self.duration = duration
        if rate is not None:
            self.rate = max(0.0, min(1.0, rate))

    # Проверить, отключено ли устройствo
    def is_disconnected(self) -> bool:
        return self._is_disconnected