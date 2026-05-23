from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator 
import yaml
import tempfile



# Конфигурация одного датчика
class SensorConfig(BaseModel):
    type: str
    name: Optional[str] = None
    initial: float = 0.0
    noise_std: float = 0.0
    trend: Optional[str] = None
    correlation_with: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    @field_validator('type')
    @classmethod
    def type_must_be_supported(cls, v: str) -> str:
        supported = ['temperature', 'humidity', 'binary', 'counter']
        if v not in supported:
            raise ValueError(f'Unsupported sensor type: {v}. Supported: {supported}')
        return v
    

# MQTT конфигурация устройства
class MQTTConfig(BaseModel):
    broker: str = "localhost:1883"
    telemetry_topic: str
    command_topic: Optional[str] = None
    qos: int = 0

# Полная конфигурация одного устройства
class DeviceConfig(BaseModel):
    id: str
    mqtt: MQTTConfig
    sensors: List[SensorConfig]
    behavior_script: Optional[str] = None           # путь к файлу сценария
    publish_interval: float = 5.0                   # секунд (реальных или симулированных)
    speed_factor_override: Optional[float] = None   # если нужно замедлить конкретное устройство


# Корневая конфигурация эмулятора
class Config(BaseModel):
    devices: List[DeviceConfig]


# Загрузчик конфигураций из YAML файлов
class ConfigLoader:

    @staticmethod
    def load_from_file(file_path: str) -> Config:
        # Загрузить конфигурацию из YAML файла
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return Config(**data)

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Config:
        # Загрузить конфигурацию из словаря
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(sample_yaml)
        temp_path = f.name

    config = ConfigLoader.load_from_file(temp_path)
    print(f"Loaded {len(config.devices)} device(s):")
    for device in config.devices:
        print(f"  - {device.id}: {len(device.sensors)} sensor(s)")