import math
from typing import Optional, Dict, Any

from iot_emulator.sensors.base import BaseSensor


class TemperatureSensor(BaseSensor):
    """
    Датчик температуры с инерцией.
    Меняется плавно к целевой температуре.
    """

    def __init__(
        self,
        name: str = "temperature",
        initial_value: float = 22.0,
        noise_std: float = 0.3,
        inertia: float = 0.1,  # Скорость изменения (0..1)
        min_value: Optional[float] = -10.0,
        max_value: Optional[float] = 50.0
    ):
        super().__init__(name, initial_value, noise_std)
        self.inertia = inertia
        self.min_value = min_value
        self.max_value = max_value
        self._target_value = initial_value

    def set_target(self, target: float) -> None:
        """Установить целевую температуру"""
        if self.min_value is not None:
            target = max(self.min_value, target)
        if self.max_value is not None:
            target = min(self.max_value, target)
        self._target_value = target

    async def update(self, delta_time: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Обновить температуру с учётом инерции.
        
        Формула: value = value + (target - value) * inertia * delta_time
        """
        # Ограничиваем delta_time, чтобы избежать резких скачков
        dt = min(delta_time, 10.0)
        
        # Плавное движение к целевой температуре
        change = (self._target_value - self._value) * self.inertia * dt
        self._value += change
        
        # Ограничения
        if self.min_value is not None:
            self._value = max(self.min_value, self._value)
        if self.max_value is not None:
            self._value = min(self.max_value, self._value)
        
        # Добавляем шум
        result = self._add_noise(self._value)
        
        return result