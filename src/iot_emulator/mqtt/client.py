import asyncio
import logging
from typing import Optional, Callable, Awaitable
from contextlib import asynccontextmanager

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Асинхронная обёртка над paho-mqtt.
    Позволяет подключаться, публиковать сообщения и подписываться на топики.
    """

    def __init__(self, client_id: str, host: str = "localhost", port: int = 1883):
        self.client_id = client_id
        self.host = host
        self.port = port
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _on_connect(self, client, userdata, flags, rc):
        """Callback при подключении к брокеру"""
        if rc == 0:
            self._connected = True
            logger.info(f"[{self.client_id}] Connected to MQTT broker at {self.host}:{self.port}")
        else:
            self._connected = False
            logger.error(f"[{self.client_id}] Failed to connect, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback при отключении от брокера"""
        self._connected = False
        logger.warning(f"[{self.client_id}] Disconnected from MQTT broker (rc: {rc})")

    def _on_publish(self, client, userdata, mid):
        """Callback при успешной публикации"""
        logger.debug(f"[{self.client_id}] Message published (mid: {mid})")

    async def connect(self) -> bool:
        """
        Подключиться к MQTT брокеру.
        Возвращает True при успешном подключении.
        """
        self._loop = asyncio.get_running_loop()
        
        # Создаём клиент
        self._client = mqtt.Client(
            client_id=self.client_id,
            protocol=mqtt.MQTTv311
        )
        
        # Назначаем callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        
        # Подключаемся (неблокирующий вызов)
        self._client.connect_async(self.host, self.port, keepalive=60)
        
        # Запускаем сетевой цикл в отдельном потоке
        self._client.loop_start()
        
        # Ждём подключения (максимум 5 секунд)
        for _ in range(50):
            if self._connected:
                return True
            await asyncio.sleep(0.1)
        
        logger.error(f"[{self.client_id}] Connection timeout")
        return False

    async def disconnect(self) -> None:
        """Отключиться от брокера"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self._connected = False
        logger.info(f"[{self.client_id}] Disconnected from MQTT broker")

    async def publish(
        self,
        topic: str,
        payload: str,
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        Опубликовать сообщение в топик.
        Возвращает True при успешной публикации.
        """
        if not self._connected or not self._client:
            logger.warning(f"[{self.client_id}] Cannot publish: not connected")
            return False
        
        try:
            # publish - неблокирующий вызов
            result = self._client.publish(topic, payload, qos=qos, retain=retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"[{self.client_id}] Published to {topic}: {payload[:50]}...")
                return True
            else:
                logger.error(f"[{self.client_id}] Publish failed, rc={result.rc}")
                return False
        except Exception as e:
            logger.error(f"[{self.client_id}] Publish error: {e}")
            return False

    def is_connected(self) -> bool:
        """Проверить, подключен ли клиент"""
        return self._connected


class MQTTClientPool:
    """
    Пул MQTT клиентов (опционально — для переиспользования соединений).
    В базовой версии не используется, так как каждое устройство имеет свой клиент.
    """

    def __init__(self, default_host: str = "localhost", default_port: int = 1883):
        self.default_host = default_host
        self.default_port = default_port
        self._clients: dict[str, MQTTClient] = {}

    async def get_client(self, client_id: str, host: str = None, port: int = None) -> MQTTClient:
        """Получить или создать клиент для указанного ID"""
        if client_id not in self._clients:
            h = host or self.default_host
            p = port or self.default_port
            client = MQTTClient(client_id, h, p)
            await client.connect()
            self._clients[client_id] = client
        return self._clients[client_id]

    async def disconnect_all(self) -> None:
        """Отключить всех клиентов"""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()