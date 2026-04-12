import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseSensor(ABC):
    """
    Базовый абстрактный класс для всех датчиков.
    """

    def __init__(self, name: str, initial_value: float = 0.0, noise_std: float = 0.0):
        self.name = name
        self._value = initial_value
        self._initial_value = initial_value
        self.noise_std = noise_std

    @abstractmethod
    async def update(self, delta_time: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Обновить показание датчика.
        
        Args:
            delta_time: Время, прошедшее с последнего обновления (в секундах)
            context: Контекст (например, значения других датчиков для корреляции)
        
        Returns:
            Текущее значение датчика
        """
        pass

    def _add_noise(self, value: float) -> float:
        """Добавить гауссов шум к значению"""
        if self.noise_std > 0:
            noise = random.gauss(0, self.noise_std)
            return value + noise
        return value

    def get_value(self) -> float:
        """Получить текущее значение датчика"""
        return self._value

    def reset(self) -> None:
        """Сбросить датчик к начальному значению"""
        self._value = self._initial_value