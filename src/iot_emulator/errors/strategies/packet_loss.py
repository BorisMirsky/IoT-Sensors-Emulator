import random
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Стратегия потери пакетов. С вероятностью rate сообщение не будет отправлено.
class PacketLossStrategy:

    def __init__(self, rate: float = 0.1):
        self.rate = max(0.0, min(1.0, rate))    #  Вероятность потери пакета (0.0 - 1.0)

    def apply(self, payload: Any) -> bool:
        # Returns: True - сообщение можно отправлять, False - сообщение потеряно (не отправлять)
        if random.random() < self.rate:
            logger.debug(f"Packet loss: message dropped (rate={self.rate})")
            return False
        return True

    # Обновить вероятность потери пакетов
    def update_rate(self, rate: float) -> None:
        self.rate = max(0.0, min(1.0, rate))