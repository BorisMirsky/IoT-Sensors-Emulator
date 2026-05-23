from typing import Dict, Type, Any
from iot_emulator.sensors.base import BaseSensor
from iot_emulator.sensors.temperature import TemperatureSensor
from iot_emulator.sensors.humidity import HumiditySensor
from iot_emulator.sensors.binary import BinarySensor
from iot_emulator.sensors.counter import CounterSensor

# Реестр доступных типов датчиков
class SensorRegistry:
    _sensors: Dict[str, Type[BaseSensor]] = {
        "temperature": TemperatureSensor,
        "humidity": HumiditySensor,
        "binary": BinarySensor,
        "counter": CounterSensor,
    }
    
    @classmethod
    def register(cls, name: str, sensor_class: Type[BaseSensor]) -> None:    # Зарегистрировать новый тип датчик
        cls._sensors[name] = sensor_class
    
    @classmethod
    def create(cls, sensor_type: str, **kwargs) -> BaseSensor:       # Создать датчик указанного типа
        if sensor_type not in cls._sensors:
            raise ValueError(f"Unknown sensor type: {sensor_type}. Available: {list(cls._sensors.keys())}")
        
        sensor_class = cls._sensors[sensor_type]
        return sensor_class(**kwargs)
    
    @classmethod
    def get_available_types(cls) -> list:
        return list(cls._sensors.keys())     # олучить список доступных типов датчиков