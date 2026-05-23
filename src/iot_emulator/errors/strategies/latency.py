import asyncio
import random
import logging
from typing import Any

logger = logging.getLogger(__name__)


# Стратегия задержки сообщений. Добавляет случайную задержку перед отправкой.
class LatencyStrategy:

    def __init__(self, min_delay: float = 0.5, max_delay: float = 3.0, rate: float = 1.0):
        self.min_delay = min_delay             #  Минимальная задержка в секундах
        self.max_delay = max_delay              # Максимальная задержка в секундах
        self.rate = max(0.0, min(1.0, rate))    # Вероятность применения задержки (0.0 - 1.0)

    # Применить стратегию (асинхронная задержка).
    async def apply(self, payload: Any) -> None:
        if random.random() < self.rate:
            delay = random.uniform(self.min_delay, self.max_delay)
            logger.debug(f"Latency: adding {delay:.2f}s delay")
            await asyncio.sleep(delay)

    # Обновить параметры задержки
    def update_params(self, min_delay: float = None, max_delay: float = None, rate: float = None) -> None:
        if min_delay is not None:
            self.min_delay = min_delay
        if max_delay is not None:
            self.max_delay = max_delay
        if rate is not None:
            self.rate = max(0.0, min(1.0, rate))