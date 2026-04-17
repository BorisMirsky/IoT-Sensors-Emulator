import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)


class TelemetryLogger:
    """
    Логгер телеметрии в формате JSON Lines.
    Каждая строка файла — отдельное JSON-сообщение.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self._current_file: Optional[Path] = None
        self._file_handle = None
        self._is_enabled = True
        self._write_lock = asyncio.Lock()

    def _get_log_filename(self) -> Path:
        """Получить имя файла лога на основе текущей даты"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.log_dir / f"telemetry_{timestamp}.jsonl"

    async def start(self) -> None:
        """Начать логирование (создать новый файл)"""
        self._current_file = self._get_log_filename()
        self._file_handle = open(self._current_file, 'w', encoding='utf-8')
        logger.info(f"Telemetry logging started: {self._current_file}")

    async def log(self, device_id: str, topic: str, payload: str, simulated_time: float) -> None:
        """
        Записать одно сообщение телеметрии в лог.
        
        Args:
            device_id: ID устройства
            topic: MQTT топик
            payload: Тело сообщения (JSON строка)
            simulated_time: Симулированное время в секундах
        """
        if not self._is_enabled or not self._file_handle:
            return
        
        async with self._write_lock:
            try:
                # Парсим payload, если он строка
                try:
                    payload_data = json.loads(payload)
                except:
                    payload_data = payload
                
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "simulated_time": simulated_time,
                    "device_id": device_id,
                    "topic": topic,
                    "payload": payload_data
                }
                
                self._file_handle.write(json.dumps(log_entry) + "\n")
                self._file_handle.flush()
                
            except Exception as e:
                logger.error(f"Failed to log telemetry: {e}")

    async def stop(self) -> None:
        """Остановить логирование и закрыть файл"""
        self._is_enabled = False
        
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
            logger.info(f"Telemetry logging stopped: {self._current_file}")

    def set_enabled(self, enabled: bool) -> None:
        """Включить/выключить логирование"""
        self._is_enabled = enabled
        logger.info(f"Telemetry logging enabled: {enabled}")