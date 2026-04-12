import random
import math
from typing import Optional


class NoiseGenerator:
    """Генераторы шума для датчиков"""
    
    @staticmethod
    def gaussian(mean: float = 0.0, std: float = 1.0) -> float:
        """Гауссов (нормальный) шум"""
        return random.gauss(mean, std)
    
    @staticmethod
    def uniform(min_val: float = -1.0, max_val: float = 1.0) -> float:
        """Равномерный шум"""
        return random.uniform(min_val, max_val)
    
    @staticmethod
    def random_walk(step_size: float = 0.1, current: float = 0.0) -> float:
        """Случайное блуждание (для дрейфа)"""
        return current + random.gauss(0, step_size)