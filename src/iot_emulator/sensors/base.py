import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# Базовый абстрактный класс для всех датчиков.
class BaseSensor(ABC):
    def __init__(self, name: str, initial_value: float = 0.0, noise_std: float = 0.0):
        self.name = name
        self._value = initial_value
        self._initial_value = initial_value
        self.noise_std = noise_std

    # Обновить показание датчика.
    @abstractmethod
    async def update(self, 
                     delta_time: float,  # Время, прошедшее с последнего обновления (в секундах)
                     context: Optional[Dict[str, Any]] = None  # Контекст (например, значения других датчиков для корреляции)
                     ) -> float:
        # returns: Текущее значение датчика
        pass

    # Добавить гауссов шум к значению
    def _add_noise(self, value: float) -> float:
        if self.noise_std > 0:
            noise = random.gauss(0, self.noise_std)
            return value + noise
        return value

    # Получить текущее значение датчика
    def get_value(self) -> float:
        return self._value

    # Сбросить датчик к начальному значению
    def reset(self) -> None:
        self._value = self._initial_value