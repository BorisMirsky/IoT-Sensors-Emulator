import asyncio
import logging
from typing import Dict, Any, Optional
from typing import TYPE_CHECKING
from datetime import datetime
from iot_emulator.utils.config_loader import DeviceConfig
from iot_emulator.time_simulation import get_simulated_sleep
from iot_emulator.sensors import SensorRegistry
from iot_emulator.behavior import BehaviorScript, load_behavior_from_file




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
        
        # Загружаем сценарий поведения (если указан)
        self._behavior: Optional[BehaviorScript] = None
        if config.behavior_script:
            self._behavior = load_behavior_from_file(config.behavior_script)
            if self._behavior:
                logger.info(f"Device {self.id} loaded behavior from {config.behavior_script}")
        
        # Создаём датчики
        self._sensors = []
        self._last_update_time: Optional[float] = None
        self._sensor_objects = {}  # name -> sensor object для доступа к set_target
        
        for sensor_cfg in config.sensors:
            sensor = SensorRegistry.create(
                sensor_cfg.type,
                name=sensor_cfg.type,
                initial_value=sensor_cfg.initial,
                noise_std=sensor_cfg.noise_std
            )
            self._sensors.append(sensor)
            self._sensor_objects[sensor_cfg.type] = sensor
        
        self._message_count = 0
        self._last_command: Optional[str] = None


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
        Обновление показаний всех датчиков и применение правил поведения.
        """
        from iot_emulator.time_simulation import get_simulated_time
        
        st = get_simulated_time()
        current_time = st.get_current_time()
        
        if self._last_update_time is None:
            self._last_update_time = current_time
            return
        
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # Собираем текущие значения датчиков для контекста
        context = {
            "simulated_time": current_time,
            "sensor_values": {sensor.name: sensor.get_value() for sensor in self._sensors},
            "last_command": self._last_command
        }
        
        # Применяем правила поведения
        if self._behavior:
            actions = self._behavior.evaluate(context)
            for action in actions:
                await self._apply_action(action)
        
        # Обновляем каждый датчик
        for sensor in self._sensors:
            await sensor.update(delta_time, context=context)
        
        # Обновляем словарь для публикации
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


    async def stop(self, timeout: float = 5.0) -> None:
        """
        Остановить устройство (graceful shutdown).
        
        Args:
            timeout: Максимальное время ожидания завершения текущей итерации
        """
        if not self._is_running:
            logger.warning(f"Device {self.id} not running")
            return
        
        logger.info(f"Stopping device {self.id}...")
        self._is_running = False
        
        if self._task and not self._task.done():
            try:
                # Ждём завершения с таймаутом
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Device {self.id} did not stop gracefully, cancelling...")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
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
    

    async def _apply_action(self, action: Dict[str, Any]) -> None:

        """Применить действие от сценария поведения"""
        action_type = action.get("type", "set_target")
        
        if action_type == "set_target":
            sensor_name = action.get("sensor")
            target_value = action.get("value")
            if sensor_name and target_value is not None:
                sensor = self._sensor_objects.get(sensor_name)
                if sensor and hasattr(sensor, 'set_target'):
                    sensor.set_target(target_value)
                    logger.info(f"[{self.id}] Set target for {sensor_name} to {target_value}")
        
        elif action_type == "add_offset":
            sensor_name = action.get("sensor")
            offset = action.get("offset", 0)
            if sensor_name:
                sensor = self._sensor_objects.get(sensor_name)
                if sensor:
                    current = sensor.get_value()
                    new_target = current + offset
                    if hasattr(sensor, 'set_target'):
                        sensor.set_target(new_target)
                        logger.info(f"[{self.id}] Added offset {offset} to {sensor_name}")
        
        elif action_type == "publish_alert":
            message = action.get("message", "Alert!")
            logger.warning(f"[{self.id}] ALERT: {message}")
            # TODO: можно отправить alert в отдельный MQTT топик
        
        elif action_type == "change_interval":
            new_interval = action.get("interval")
            if new_interval:
                self.config.publish_interval = float(new_interval)
                logger.info(f"[{self.id}] Publish interval changed to {new_interval}s")



    async def handle_command(self, command: str, payload: Dict[str, Any]) -> None:
        """
        Обработать команду, полученную через MQTT.
        """
        self._last_command = command
        logger.info(f"[{self.id}] Received command: {command} with payload {payload}")
        
        # Базовая обработка встроенных команд
        if command == "set_target":
            sensor_name = payload.get("sensor")
            value = payload.get("value")
            if sensor_name and value is not None:
                sensor = self._sensor_objects.get(sensor_name)
                if sensor and hasattr(sensor, 'set_target'):
                    sensor.set_target(float(value))
                    logger.info(f"[{self.id}] Set target for {sensor_name} to {value}")
        
        elif command == "change_interval":
            new_interval = payload.get("interval")
            if new_interval:
                self.config.publish_interval = float(new_interval)
                logger.info(f"[{self.id}] Publish interval changed to {new_interval}s")