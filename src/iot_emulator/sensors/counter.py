from typing import Optional, Dict, Any

from iot_emulator.sensors.base import BaseSensor


class CounterSensor(BaseSensor):
    """
    Счётчик (например, счётчик воды, электричества).
    Монотонно возрастает.
    """

    def __init__(
        self,
        name: str = "counter",
        initial_value: float = 0.0,
        increment_rate: float = 0.01,  # Единиц в секунду
        noise_std: float = 0.1
    ):
        super().__init__(name, initial_value, noise_std)
        self.increment_rate = increment_rate

    async def update(self, delta_time: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Обновить счётчик.
        Монотонно увеличивается с заданной скоростью.
        """
        dt = min(delta_time, 10.0)
        
        # Увеличиваем счётчик
        self._value += self.increment_rate * dt
        
        # Добавляем шум (может быть отрицательным, но счётчик не уменьшается)
        noisy_value = self._add_noise(self._value)
        
        # Счётчик не может уменьшаться
        result = max(noisy_value, self._value - 0.1)
        self._value = result
        
        return result