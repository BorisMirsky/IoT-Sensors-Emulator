import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from iot_emulator.utils.config_loader import DeviceConfig
from iot_emulator.time_simulation import get_simulated_sleep

logger = logging.getLogger(__name__)


class Device:
    """
    Базовое IoT-устройство.
    Пока без MQTT — просто выводит данные в консоль.
    """

    def __init__(self, config: DeviceConfig):
        self.config = config
        self.id = config.id
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._simulated_sleep = get_simulated_sleep()
        
        # Состояние датчиков (пока просто заглушка)
        self._sensor_values: Dict[str, float] = {}
        for sensor in config.sensors:
            self._sensor_values[sensor.type] = sensor.initial
        
        self._message_count = 0

    async def _publish_telemetry(self) -> None:
        """
        Публикация телеметрии.
        Пока только print, позже заменим на реальный MQTT.
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{self.id}] TELEMETRY: {self._sensor_values}")
        self._message_count += 1

    async def _update_sensors(self) -> None:
        """
        Обновление показаний датчиков.
        Пока просто заглушка — симуляции нет.
        TODO: пункт 6 добавит реальную логику с шумом и трендами.
        """
        # Пока оставляем значения неизменными
        pass

    async def _run_loop(self) -> None:
        """
        Основной цикл устройства:
        sleep → обновить датчики → опубликовать телеметрию → повторить
        """
        interval = self.config.publish_interval
        logger.info(f"Device {self.id} started with interval {interval}s")
        
        while self._is_running:
            try:
                # Ждём интервал в симулированном времени
                await self._simulated_sleep(interval)
                
                # Обновляем показания датчиков
                await self._update_sensors()
                
                # Публикуем телеметрию
                await self._publish_telemetry()
                
            except asyncio.CancelledError:
                logger.info(f"Device {self.id} cancelled")
                break
            except Exception as e:
                logger.error(f"Device {self.id} error: {e}")
                await asyncio.sleep(1)  # Не спамим ошибками

    def start(self) -> None:
        """Запустить устройство"""
        if self._is_running:
            logger.warning(f"Device {self.id} already running")
            return
        
        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Device {self.id} task created")

    async def stop(self) -> None:
        """Остановить устройство (graceful shutdown)"""
        if not self._is_running:
            logger.warning(f"Device {self.id} not running")
            return
        
        self._is_running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Device {self.id} stopped. Published {self._message_count} messages")

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику устройства"""
        return {
            "device_id": self.id,
            "is_running": self._is_running,
            "message_count": self._message_count,
            "sensor_values": self._sensor_values.copy(),
        }