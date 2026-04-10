import asyncio
import time
from typing import Optional


class SimulatedTime:
    """
    Глобальный контроллер симулированного времени.
    Позволяет ускорять/замедлять время относительно реального.
    
    Пример: speed_factor = 60.0 означает, что 1 реальная секунда = 1 симулированная минута.
    """

    _instance: Optional['SimulatedTime'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SimulatedTime':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._speed_factor: float = 1.0
        self._start_real_time: float = 0.0
        self._start_simulated_time: float = 0.0
        self._is_running: bool = False
        self._paused_simulated_time: float = 0.0

    def start(self, speed_factor: float = 1.0) -> None:
        """Запустить симуляцию времени с указанным коэффициентом ускорения"""
        self._speed_factor = speed_factor
        self._start_real_time = time.monotonic()
        
        if self._is_running:
            # Если уже запущено, продолжаем с текущего симулированного времени
            self._start_simulated_time = self._paused_simulated_time
        else:
            self._start_simulated_time = 0.0
            self._paused_simulated_time = 0.0
        
        self._is_running = True

    def pause(self) -> None:
        """Приостановить симуляцию времени"""
        if self._is_running:
            self._paused_simulated_time = self.get_current_time()
            self._is_running = False

    def resume(self) -> None:
        """Возобновить симуляцию времени"""
        if not self._is_running:
            self._start_real_time = time.monotonic()
            self._start_simulated_time = self._paused_simulated_time
            self._is_running = True

    def stop(self) -> None:
        """Остановить симуляцию и сбросить время"""
        self._is_running = False
        self._start_real_time = 0.0
        self._start_simulated_time = 0.0
        self._paused_simulated_time = 0.0

    def get_current_time(self) -> float:
        """
        Получить текущее симулированное время (в секундах).
        Если симуляция не запущена — возвращает последнее известное время.
        """
        if not self._is_running:
            return self._paused_simulated_time
        
        real_elapsed = time.monotonic() - self._start_real_time
        return self._start_simulated_time + (real_elapsed * self._speed_factor)

    def set_speed_factor(self, speed_factor: float) -> None:
        """Изменить коэффициент ускорения на лету"""
        if speed_factor <= 0:
            raise ValueError("Speed factor must be positive")
        
        # Сохраняем текущее симулированное время
        current_simulated = self.get_current_time()
        
        # Перезапускаем с новым коэффициентом
        self._start_real_time = time.monotonic()
        self._start_simulated_time = current_simulated
        self._speed_factor = speed_factor
        self._is_running = True

    def get_speed_factor(self) -> float:
        """Получить текущий коэффициент ускорения"""
        return self._speed_factor

    def is_running(self) -> bool:
        """Запущена ли симуляция"""
        return self._is_running


class SimulatedSleep:
    """
    Асинхронный sleep, работающий в симулированном времени.
    Использование: await simulated_sleep(duration_seconds, speed_factor)
    """

    def __init__(self, simulated_time: SimulatedTime):
        self._simulated_time = simulated_time

    async def __call__(self, duration: float) -> None:
        """
        Усыпить корутину на duration секунд симулированного времени.
        """
        if duration <= 0:
            return
        
        start_simulated = self._simulated_time.get_current_time()
        target_simulated = start_simulated + duration
        
        while self._simulated_time.get_current_time() < target_simulated:
            # Вычисляем, сколько реального времени осталось ждать
            remaining_simulated = target_simulated - self._simulated_time.get_current_time()
            if remaining_simulated <= 0:
                break
            
            speed = self._simulated_time.get_speed_factor()
            # Конвертируем симулированное время в реальное
            real_wait = remaining_simulated / speed if speed > 0 else 0.1
            
            # Ждём небольшими порциями, чтобы можно было реагировать на изменение speed_factor
            await asyncio.sleep(min(real_wait, 0.1))


# Глобальный синглтон для удобного импорта
_simulated_time = SimulatedTime()

def get_simulated_time() -> SimulatedTime:
    """Получить глобальный экземпляр SimulatedTime"""
    return _simulated_time

def get_simulated_sleep():
    """Получить функцию для сна в симулированном времени"""
    return SimulatedSleep(_simulated_time)


# Пример использования (для теста)
if __name__ == "__main__":
    import asyncio
    
    async def test():
        st = get_simulated_time()
        sleep = get_simulated_sleep()
        
        print("Запуск симуляции с ускорением 60x (1 сек реального = 1 мин симулированного)")
        st.start(speed_factor=60.0)
        
        print(f"Симулированное время: {st.get_current_time():.1f} сек")
        await sleep(30.0)  # ждём 30 симулированных секунд (0.5 реальных)
        print(f"После сна 30 сек: {st.get_current_time():.1f} сек")
        
        st.pause()
        print(f"Пауза. Время заморожено: {st.get_current_time():.1f} сек")
        await asyncio.sleep(1.0)
        print(f"После 1 реальной секунды паузы: {st.get_current_time():.1f} сек")
        
        st.resume()
        print("Возобновление")
        await sleep(30.0)
        print(f"После ещё 30 сек: {st.get_current_time():.1f} сек")
        
        st.stop()
    
    asyncio.run(test())