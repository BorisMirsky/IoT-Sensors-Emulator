import asyncio
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class DisconnectStrategy:
    """
    Стратегия отключения устройства.
    Эмулирует временную потерю связи.
    """

    def __init__(self, duration: float = 5.0, rate: float = 0.01):
        """
        Args:
            duration: Длительность отключения в секундах
            rate: Вероятность отключения за одну публикацию
        """
        self.duration = duration
        self.rate = rate
        self._is_disconnected = False
        self._disconnect_callback: Optional[Callable] = None
        self._reconnect_callback: Optional[Callable] = None

    def set_callbacks(self, on_disconnect: Callable, on_reconnect: Callable) -> None:
        """Установить callback для отключения/подключения"""
        self._disconnect_callback = on_disconnect
        self._reconnect_callback = on_reconnect

    async def check_and_apply(self) -> bool:
        """
        Проверить, нужно ли отключиться/подключиться.
        
        Returns:
            True - устройство отключено
            False - устройство работает нормально
        """
        if not self._is_disconnected:
            # Проверяем, нужно ли отключиться
            import random
            if random.random() < self.rate:
                self._is_disconnected = True
                logger.warning(f"Disconnect strategy: disconnecting for {self.duration}s")
                if self._disconnect_callback:
                    await self._disconnect_callback()
                # Запускаем таймер на подключение
                asyncio.create_task(self._reconnect_after_delay())
                return True
        return self._is_disconnected

    async def _reconnect_after_delay(self) -> None:
        """Подключиться после задержки"""
        await asyncio.sleep(self.duration)
        self._is_disconnected = False
        logger.info("Disconnect strategy: reconnected")
        if self._reconnect_callback:
            await self._reconnect_callback()

    def update_params(self, duration: float = None, rate: float = None) -> None:
        """Обновить параметры отключения"""
        if duration is not None:
            self.duration = duration
        if rate is not None:
            self.rate = max(0.0, min(1.0, rate))

    def is_disconnected(self) -> bool:
        """Проверить, отключено ли устройство"""
        return self._is_disconnected