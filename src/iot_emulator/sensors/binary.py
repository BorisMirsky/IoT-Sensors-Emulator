import random
from typing import Optional, Dict, Any

from iot_emulator.sensors.base import BaseSensor


class BinarySensor(BaseSensor):
    """
    Бинарный датчик (0 или 1).
    Например: движение, дверь открыта/закрыта, реле.
    """

    def __init__(
        self,
        name: str = "binary",
        initial_value: float = 0.0,
        noise_std: float = 0.0,  # Бинарные датчики обычно без шума
        toggle_probability: float = 0.001  # Вероятность смены состояния в секунду
    ):
        super().__init__(name, initial_value, noise_std)
        self.toggle_probability = toggle_probability

    async def update(self, delta_time: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Обновить бинарное состояние.
        Случайно переключается с вероятностью toggle_probability * delta_time.
        """
        dt = min(delta_time, 10.0)
        
        # Вероятность переключения за этот интервал
        prob = self.toggle_probability * dt
        
        if random.random() < prob:
            self._value = 1.0 if self._value < 0.5 else 0.0
        
        return self._value