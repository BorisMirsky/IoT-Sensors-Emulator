from typing import Optional, Dict, Any

from iot_emulator.sensors.base import BaseSensor


class HumiditySensor(BaseSensor):
    """
    Датчик влажности.
    Может быть коррелирован с температурой.
    """

    def __init__(
        self,
        name: str = "humidity",
        initial_value: float = 55.0,
        noise_std: float = 2.0,
        correlation_with: Optional[str] = None,  # имя датчика температуры
        min_value: Optional[float] = 0.0,
        max_value: Optional[float] = 100.0
    ):
        super().__init__(name, initial_value, noise_std)
        self.correlation_with = correlation_with
        self.min_value = min_value
        self.max_value = max_value

    async def update(self, delta_time: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Обновить влажность.
        Если есть корреляция с температурой — вычисляем на основе неё.
        """
        # Если есть корреляция и в контексте есть значение температуры
        if self.correlation_with and context:
            temp_value = context.get(self.correlation_with)
            if temp_value is not None:
                # Простая корреляция: при повышении температуры на 1°C, 
                # влажность может немного меняться (упрощённая модель)
                # Базовая влажность 55% при 22°C
                base_humidity = 55.0 - (temp_value - 22.0) * 0.5
                self._value = base_humidity
        
        # Естественная инерция (медленное изменение к среднему)
        dt = min(delta_time, 10.0)
        self._value = self._value + (55.0 - self._value) * 0.05 * dt
        
        # Ограничения
        if self.min_value is not None:
            self._value = max(self.min_value, self._value)
        if self.max_value is not None:
            self._value = min(self.max_value, self._value)
        
        # Добавляем шум
        result = self._add_noise(self._value)
        
        return result