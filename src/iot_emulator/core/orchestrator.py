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
        
        from iot_emulator.time_simulation import get_simulated_time
        from iot_emulator.mqtt import MQTTClient
        
        # Запускаем глобальное время
        st = get_simulated_time()
        st.start(speed_factor=speed_factor)
        logger.info(f"Simulated time started with speed factor: {speed_factor}")
        
        # Создаём и запускаем устройства
        for device_config in self._config.devices:
            if device_config.id in self._devices:
                logger.warning(f"Device {device_config.id} already exists, skipping")
                continue
            
            # Создаём MQTT-клиент для устройства
            broker = device_config.mqtt.broker
            host, port = self._parse_broker_address(broker)
            mqtt_client = MQTTClient(
                client_id=f"emulator_{device_config.id}",
                host=host,
                port=port
            )
            await mqtt_client.connect()
            
            # Создаём устройство
            device = Device(device_config, mqtt_client=mqtt_client)
            self._devices[device_config.id] = device
            device.start()
            logger.info(f"Device {device_config.id} started")
        
        await asyncio.sleep(0.1)
    
    def _parse_broker_address(self, address: str) -> tuple[str, int]:
        """Разобрать адрес брокера 'host:port' -> (host, port)"""
        parts = address.split(':')
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 1883
        return host, port


    async def stop_all(self) -> None:
        """Остановить все устройства"""
        logger.info("Stopping all devices...")
        
        # Останавливаем все устройства параллельно
        tasks = [device.stop() for device in self._devices.values()]
        await asyncio.gather(*tasks)
        
        # Отключаем MQTT-клиенты
        for device in self._devices.values():
            if hasattr(device, '_mqtt_client') and device._mqtt_client:
                await device._mqtt_client.disconnect()
        
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