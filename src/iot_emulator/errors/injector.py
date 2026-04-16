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


class ErrorInjector:
    """
    Инжектор ошибок для устройства.
    Управляет стратегиями ошибок и применяет их к сообщениям.
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        self._strategies: Dict[ErrorType, Any] = {}
        self._active_errors: Dict[ErrorType, bool] = {}

    def add_packet_loss(self, rate: float = 0.1) -> None:
        """Добавить стратегию потери пакетов"""
        self._strategies[ErrorType.PACKET_LOSS] = PacketLossStrategy(rate)
        self._active_errors[ErrorType.PACKET_LOSS] = True
        logger.info(f"[{self.device_id}] Added packet loss error (rate={rate})")

    def add_latency(self, min_delay: float = 0.5, max_delay: float = 3.0, rate: float = 1.0) -> None:
        """Добавить стратегию задержки"""
        self._strategies[ErrorType.LATENCY] = LatencyStrategy(min_delay, max_delay, rate)
        self._active_errors[ErrorType.LATENCY] = True
        logger.info(f"[{self.device_id}] Added latency error (delay={min_delay}-{max_delay}s, rate={rate})")

    def add_disconnect(self, duration: float = 5.0, rate: float = 0.01) -> None:
        """Добавить стратегию отключения"""
        self._strategies[ErrorType.DISCONNECT] = DisconnectStrategy(duration, rate)
        self._active_errors[ErrorType.DISCONNECT] = True
        logger.info(f"[{self.device_id}] Added disconnect error (duration={duration}s, rate={rate})")

    def remove_error(self, error_type: ErrorType) -> None:
        """Удалить стратегию ошибки"""
        if error_type in self._strategies:
            del self._strategies[error_type]
        self._active_errors[error_type] = False
        logger.info(f"[{self.device_id}] Removed error: {error_type.value}")

    def remove_all_errors(self) -> None:
        """Удалить все ошибки"""
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

    def set_disconnect_callbacks(self, on_disconnect, on_reconnect) -> None:
        """Установить callbacks для стратегии отключения"""
        if ErrorType.DISCONNECT in self._strategies:
            self._strategies[ErrorType.DISCONNECT].set_callbacks(on_disconnect, on_reconnect)

    def get_active_errors(self) -> list:
        """Получить список активных ошибок"""
        return [e.value for e in self._strategies.keys()]

    def update_packet_loss_rate(self, rate: float) -> None:
        """Обновить вероятность потери пакетов"""
        if ErrorType.PACKET_LOSS in self._strategies:
            self._strategies[ErrorType.PACKET_LOSS].update_rate(rate)
            logger.info(f"[{self.device_id}] Updated packet loss rate to {rate}")

    def update_latency_params(self, min_delay: float = None, max_delay: float = None, rate: float = None) -> None:
        """Обновить параметры задержки"""
        if ErrorType.LATENCY in self._strategies:
            self._strategies[ErrorType.LATENCY].update_params(min_delay, max_delay, rate)
            logger.info(f"[{self.device_id}] Updated latency params")