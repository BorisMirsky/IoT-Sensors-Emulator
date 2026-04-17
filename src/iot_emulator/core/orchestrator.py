import asyncio
import logging
import signal
from typing import Dict, List, Optional, Set

from iot_emulator.core.device import Device
from iot_emulator.utils.config_loader import Config, DeviceConfig
from iot_emulator.logging import TelemetryLogger


logger = logging.getLogger(__name__)


class DeviceOrchestrator:
    """
    Оркестратор устройств — управляет запуском, остановкой,
    graceful shutdown и сбором статистики.
    """

    def __init__(self):
        self._devices: Dict[str, Device] = {}
        self._config: Optional[Config] = None
        self._shutdown_event = asyncio.Event()
        self._shutdown_started = False
        self._telemetry_logger: Optional[TelemetryLogger] = None
        

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
        
        # Запускаем логгер телеметрии
        self._telemetry_logger = TelemetryLogger()
        await self._telemetry_logger.start()

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
            #device = Device(device_config, mqtt_client=mqtt_client)
                        # Создаём устройство
            device = Device(device_config, mqtt_client=mqtt_client, telemetry_logger=self._telemetry_logger)
            self._devices[device_config.id] = device
            device.start()
            logger.info(f"Device {device_config.id} started")
        
        # Небольшая пауза, чтобы устройства успели запуститься
        await asyncio.sleep(0.1)

    async def stop_device(self, device_id: str, graceful: bool = True) -> bool:
        """
        Остановить конкретное устройство.
        
        Args:
            device_id: ID устройства
            graceful: Если True — ждём завершения текущей итерации,
                      если False — принудительная отмена
        
        Returns:
            True если устройство было остановлено, False если не найдено
        """
        device = self._devices.get(device_id)
        if not device:
            logger.warning(f"Device {device_id} not found")
            return False
        
        logger.info(f"Stopping device {device_id} (graceful={graceful})")
        await device.stop()
        
        # Отключаем MQTT-клиент
        if hasattr(device, '_mqtt_client') and device._mqtt_client:
            await device._mqtt_client.disconnect()
        
        del self._devices[device_id]
        logger.info(f"Device {device_id} stopped and removed")
        return True

    async def stop_all(self, graceful: bool = True) -> None:
        """
        Остановить все устройства.
        
        Args:
            graceful: Если True — останавливаем все устройства параллельно с ожиданием,
                      если False — отменяем все задачи принудительно
        """
        if self._shutdown_started:
            logger.warning("Shutdown already in progress")
            return
        
        self._shutdown_started = True
        logger.info(f"Stopping all devices (graceful={graceful})...")
        
        if graceful:
            # Останавливаем все устройства параллельно
            tasks = [device.stop() for device in self._devices.values()]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Отключаем MQTT-клиенты
            for device in self._devices.values():
                if hasattr(device, '_mqtt_client') and device._mqtt_client:
                    await device._mqtt_client.disconnect()
        else:
            # Принудительная отмена всех задач
            for device in self._devices.values():
                if hasattr(device, '_task') and device._task and not device._task.done():
                    device._task.cancel()
            
            # Даём время на отмену
            await asyncio.sleep(0.5)
        
        # Останавливаем логгер телеметрии
        if self._telemetry_logger:
            await self._telemetry_logger.stop()

        self._devices.clear()
        
        # Останавливаем симуляцию времени
        from iot_emulator.time_simulation import get_simulated_time
        st = get_simulated_time()
        st.stop()
        
        logger.info("All devices stopped")
        self._shutdown_started = False

    def get_devices_status(self) -> List[dict]:
        """Получить статус всех устройств"""
        return [device.get_stats() for device in self._devices.values()]

    def get_device_stats(self, device_id: str) -> Optional[dict]:
        """Получить статистику конкретного устройства"""
        device = self._devices.get(device_id)
        if device:
            return device.get_stats()
        return None

    def get_active_device_ids(self) -> Set[str]:
        """Получить множество ID активных устройств"""
        return set(self._devices.keys())

    def _parse_broker_address(self, address: str) -> tuple:

        """Разобрать адрес брокера 'host:port' -> (host, port)"""
        parts = address.split(':')
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 1883
        return host, port
    

    def get_telemetry_logger(self) -> Optional[TelemetryLogger]:
        """Получить логгер телеметрии"""
        return self._telemetry_logger