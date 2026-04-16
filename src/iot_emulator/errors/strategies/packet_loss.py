import random
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PacketLossStrategy:
    """
    Стратегия потери пакетов.
    С вероятностью rate сообщение не будет отправлено.
    """

    def __init__(self, rate: float = 0.1):
        """
        Args:
            rate: Вероятность потери пакета (0.0 - 1.0)
        """
        self.rate = max(0.0, min(1.0, rate))

    def apply(self, payload: Any) -> bool:
        """
        Применить стратегию.
        
        Returns:
            True - сообщение можно отправлять
            False - сообщение потеряно (не отправлять)
        """
        if random.random() < self.rate:
            logger.debug(f"Packet loss: message dropped (rate={self.rate})")
            return False
        return True

    def update_rate(self, rate: float) -> None:
        """Обновить вероятность потери пакетов"""
        self.rate = max(0.0, min(1.0, rate))