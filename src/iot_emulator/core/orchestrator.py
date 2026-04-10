import asyncio
import logging
from typing import Dict, List, Optional

from iot_emulator.core.device import Device
from iot_emulator.utils.config_loader import Config, DeviceConfig

logger = logging.getLogger(__name__)


class DeviceOrchestrator:
    """
    Оркестратор устройств — управляет запуском и остановкой.
    """

    def __init__(self):
        self._devices: Dict[str, Device] = {}
        self._config: Optional[Config] = None

    def load_config(self, config: Config) -> None:
        """Загрузить конфигурацию (но не запускать устройства)"""
        self._config = config

    async def start_all(self, speed_factor: float = 1.0) -> None:
        """Запустить все устройства из конфигурации"""
        if not self._config:
            raise RuntimeError("No config loaded. Call load_config() first.")
        
        # Импортируем симуляцию времени здесь, чтобы избежать циклических импортов
        from iot_emulator.time_simulation import get_simulated_time
        
        # Запускаем глобальное время
        st = get_simulated_time()
        st.start(speed_factor=speed_factor)
        logger.info(f"Simulated time started with speed factor: {speed_factor}")
        
        # Создаём и запускаем устройства
        for device_config in self._config.devices:
            if device_config.id in self._devices:
                logger.warning(f"Device {device_config.id} already exists, skipping")
                continue
            
            device = Device(device_config)
            self._devices[device_config.id] = device
            device.start()
            logger.info(f"Device {device_config.id} started")
        
        # Небольшая пауза, чтобы устройства успели запуститься
        await asyncio.sleep(0.1)

    async def stop_all(self) -> None:
        """Остановить все устройства"""
        logger.info("Stopping all devices...")
        
        # Останавливаем все устройства параллельно
        tasks = [device.stop() for device in self._devices.values()]
        await asyncio.gather(*tasks)
        
        self._devices.clear()
        
        # Останавливаем симуляцию времени
        from iot_emulator.time_simulation import get_simulated_time
        st = get_simulated_time()
        st.stop()
        logger.info("All devices stopped")

    async def stop_device(self, device_id: str) -> bool:
        """Остановить конкретное устройство"""
        device = self._devices.get(device_id)
        if not device:
            logger.warning(f"Device {device_id} not found")
            return False
        
        await device.stop()
        del self._devices[device_id]
        logger.info(f"Device {device_id} stopped and removed")
        return True

    def get_devices_status(self) -> List[dict]:
        """Получить статус всех устройств"""
        return [device.get_stats() for device in self._devices.values()]

    def get_device_stats(self, device_id: str) -> Optional[dict]:
        """Получить статистику конкретного устройства"""
        device = self._devices.get(device_id)
        if device:
            return device.get_stats()
        return None