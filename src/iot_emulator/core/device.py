import asyncio
import logging
from typing import Dict, Any, Optional
from typing import TYPE_CHECKING
from datetime import datetime
from iot_emulator.utils.config_loader import DeviceConfig
from iot_emulator.time_simulation import get_simulated_sleep
from iot_emulator.sensors import SensorRegistry


if TYPE_CHECKING:
    from iot_emulator.mqtt.client import MQTTClient
    
logger = logging.getLogger(__name__)


class Device:
    """
    Базовое IoT-устройство.
    Пока без MQTT — просто выводит данные в консоль.
    """

    def __init__(self, config: DeviceConfig, mqtt_client: Optional['MQTTClient'] = None):
        self.config = config
        self.id = config.id
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._simulated_sleep = get_simulated_sleep()
        
        # MQTT клиент
        self._mqtt_client = mqtt_client
        
        # Создаём реальные датчики из конфигурации
        self._sensors = []
        self._last_update_time: Optional[float] = None
        
        for sensor_cfg in config.sensors:
            sensor = SensorRegistry.create(
                sensor_cfg.type,
                name=sensor_cfg.type,
                initial_value=sensor_cfg.initial,
                noise_std=sensor_cfg.noise_std
            )
            self._sensors.append(sensor)
        
        self._message_count = 0


    async def _publish_telemetry(self) -> None:
        """
        Публикация телеметрии через MQTT или print (если MQTT не доступен).
        """
        import json
        
        # Формируем payload
        payload = json.dumps({
            "device_id": self.id,
            "timestamp": self._simulated_sleep._simulated_time.get_current_time(),
            "sensors": self._sensor_values
        })
        
        topic = self.config.mqtt.telemetry_topic
        
        if self._mqtt_client and self._mqtt_client.is_connected():
            # Публикуем через MQTT
            success = await self._mqtt_client.publish(topic, payload, qos=self.config.mqtt.qos)
            if success:
                self._message_count += 1
                logger.debug(f"[{self.id}] Published to MQTT: {topic}")
            else:
                logger.warning(f"[{self.id}] MQTT publish failed")
        else:
            # Fallback на print (для тестирования без MQTT брокера)
            timestamp_str = __import__('datetime').datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp_str}] [{self.id}] TELEMETRY: {self._sensor_values}")
            self._message_count += 1


    async def _update_sensors(self) -> None:
        """
        Обновление показаний всех датчиков.
        """
        from iot_emulator.time_simulation import get_simulated_time
        
        st = get_simulated_time()
        current_time = st.get_current_time()
        
        if self._last_update_time is None:
            self._last_update_time = current_time
            return
        
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # Собираем значения всех датчиков для контекста (корреляции)
        context = {}
        for sensor in self._sensors:
            context[sensor.name] = sensor.get_value()
        
        # Обновляем каждый датчик
        for sensor in self._sensors:
            await sensor.update(delta_time, context=context)
        
        # Обновляем словарь _sensor_values для совместимости с _publish_telemetry
        self._sensor_values = {sensor.name: sensor.get_value() for sensor in self._sensors}


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