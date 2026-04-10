from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import yaml


class SensorConfig(BaseModel):
    """Конфигурация одного датчика"""
    type: str  # temperature, humidity, binary, counter
    name: Optional[str] = None
    initial: float = 0.0
    noise_std: float = 0.0
    trend: Optional[str] = None  # например: "+0.1 per hour"
    correlation_with: Optional[str] = None  # имя другого датчика
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    @validator('type')
    def type_must_be_supported(cls, v):
        supported = ['temperature', 'humidity', 'binary', 'counter']
        if v not in supported:
            raise ValueError(f'Unsupported sensor type: {v}. Supported: {supported}')
        return v


class MQTTConfig(BaseModel):
    """MQTT конфигурация устройства"""
    broker: str = "localhost:1883"
    telemetry_topic: str
    command_topic: Optional[str] = None
    qos: int = 0


class DeviceConfig(BaseModel):
    """Полная конфигурация одного устройства"""
    id: str
    mqtt: MQTTConfig
    sensors: List[SensorConfig]
    behavior_script: Optional[str] = None  # путь к файлу сценария
    publish_interval: float = 5.0  # секунд (реальных или симулированных)
    speed_factor_override: Optional[float] = None  # если нужно замедлить конкретное устройство


class Config(BaseModel):
    """Корневая конфигурация эмулятора"""
    devices: List[DeviceConfig]


class ConfigLoader:
    """Загрузчик конфигураций из YAML файлов"""

    @staticmethod
    def load_from_file(file_path: str) -> Config:
        """Загрузить конфигурацию из YAML файла"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return Config(**data)

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Config:
        """Загрузить конфигурацию из словаря"""
        return Config(**data)


# Пример использования (для теста)
if __name__ == "__main__":
    sample_yaml = """
devices:
  - id: living_room_sensor
    mqtt:
      broker: localhost:1883
      telemetry_topic: "home/living_room/sensors"
      command_topic: "home/living_room/cmd"
    sensors:
      - type: temperature
        initial: 22.5
        noise_std: 0.3
        min_value: -10
        max_value: 50
      - type: humidity
        initial: 55.0
        noise_std: 2.0
    publish_interval: 5.0

  - id: garage_door
    mqtt:
      telemetry_topic: "home/garage/sensors"
    sensors:
      - type: binary
        name: door_open
        initial: 0
    publish_interval: 1.0
"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(sample_yaml)
        temp_path = f.name

    config = ConfigLoader.load_from_file(temp_path)
    print(f"Loaded {len(config.devices)} device(s):")
    for device in config.devices:
        print(f"  - {device.id}: {len(device.sensors)} sensor(s)")