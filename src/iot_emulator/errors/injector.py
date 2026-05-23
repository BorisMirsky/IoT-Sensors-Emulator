import logging
from typing import Dict, Optional, Any
from enum import Enum

from iot_emulator.errors.strategies import (
    PacketLossStrategy,
    LatencyStrategy,
    DisconnectStrategy
)

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Типы ошибок для инъекции"""
    PACKET_LOSS = "packet_loss"
    LATENCY = "latency"
    DISCONNECT = "disconnect"


#  Инжектор ошибок для устройства. Управляет стратегиями ошибок и применяет их к сообщениям.
class ErrorInjector:

    def __init__(self, device_id: str):
        self.device_id = device_id
        self._strategies: Dict[ErrorType, Any] = {}
        self._active_errors: Dict[ErrorType, bool] = {}

    # Добавить стратегию потери пакетов
    def add_packet_loss(self, rate: float = 0.1) -> None:
        self._strategies[ErrorType.PACKET_LOSS] = PacketLossStrategy(rate)
        self._active_errors[ErrorType.PACKET_LOSS] = True
        logger.info(f"[{self.device_id}] Added packet loss error (rate={rate})")

    # Добавить стратегию задержки
    def add_latency(self, min_delay: float = 0.5, max_delay: float = 3.0, rate: float = 1.0) -> None:
        self._strategies[ErrorType.LATENCY] = LatencyStrategy(min_delay, max_delay, rate)
        self._active_errors[ErrorType.LATENCY] = True
        logger.info(f"[{self.device_id}] Added latency error (delay={min_delay}-{max_delay}s, rate={rate})")

    # Добавить стратегию отключения
    def add_disconnect(self, duration: float = 5.0, rate: float = 0.01) -> None:
        self._strategies[ErrorType.DISCONNECT] = DisconnectStrategy(duration, rate)
        self._active_errors[ErrorType.DISCONNECT] = True
        logger.info(f"[{self.device_id}] Added disconnect error (duration={duration}s, rate={rate})")

    # Удалить стратегию ошибки
    def remove_error(self, error_type: ErrorType) -> None:
        if error_type in self._strategies:
            del self._strategies[error_type]
        self._active_errors[error_type] = False
        logger.info(f"[{self.device_id}] Removed error: {error_type.value}")

    def remove_all_errors(self) -> None:
        self._strategies.clear()
        self._active_errors.clear()
        logger.info(f"[{self.device_id}] Removed all errors")

    async def apply_before_publish(self, payload: Any) -> bool:
        """
        Применить все активные стратегии перед публикацией. 
        Args:
            payload: Сообщение для публикации    
        Returns:
            True - можно публиковать
            False - публикацию нужно отменить (потеря пакета)
        """
        # Проверяем отключение
        if ErrorType.DISCONNECT in self._strategies:
            strategy = self._strategies[ErrorType.DISCONNECT]
            if await strategy.check_and_apply():
                return False  # Устройство отключено, не публикуем
        
        # Проверяем потерю пакетов
        if ErrorType.PACKET_LOSS in self._strategies:
            strategy = self._strategies[ErrorType.PACKET_LOSS]
            if not strategy.apply(payload):
                return False
        
        # Применяем задержку
        if ErrorType.LATENCY in self._strategies:
            strategy = self._strategies[ErrorType.LATENCY]
            await strategy.apply(payload)
        
        return True

    # Установить callbacks для стратегии отключения
    def set_disconnect_callbacks(self, on_disconnect, on_reconnect) -> None:
        if ErrorType.DISCONNECT in self._strategies:
            self._strategies[ErrorType.DISCONNECT].set_callbacks(on_disconnect, on_reconnect)

    def get_active_errors(self) -> list:
        return [e.value for e in self._strategies.keys()]
    
    # Обновить вероятность потери пакетов
    def update_packet_loss_rate(self, rate: float) -> None:
        if ErrorType.PACKET_LOSS in self._strategies:
            self._strategies[ErrorType.PACKET_LOSS].update_rate(rate)
            logger.info(f"[{self.device_id}] Updated packet loss rate to {rate}")

    # Обновить параметры задержки
    def update_latency_params(self, min_delay: float = None, max_delay: float = None, rate: float = None) -> None:
        if ErrorType.LATENCY in self._strategies:
            self._strategies[ErrorType.LATENCY].update_params(min_delay, max_delay, rate)
            logger.info(f"[{self.device_id}] Updated latency params")