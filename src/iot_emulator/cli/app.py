import asyncio
import typer
from typing import Optional
import signal
import logging

from iot_emulator.utils.config_loader import ConfigLoader
from iot_emulator.core.orchestrator import DeviceOrchestrator

app = typer.Typer(
    name="iot-emulator",
    help="Эмулятор IoT-устройств с MQTT и симуляцией датчиков",
    add_completion=False,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


# Глобальный оркестратор (будет инициализирован при старте)
_orchestrator: Optional[DeviceOrchestrator] = None


@app.command()
def start(
    config: str = typer.Option(..., "--config", "-c", help="Путь к YAML конфигу устройств"),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Коэффициент ускорения времени (например, 60 = 1 минута за 1 секунду)"),
    broker: str = typer.Option("localhost:1883", "--broker", "-b", help="MQTT брокер (host:port)"),
):
    """Запустить эмулятор с указанной конфигурацией"""
    global _orchestrator
    
    typer.echo(f"Загрузка конфигурации из: {config}")
    typer.echo(f"Коэффициент ускорения: {speed}x")
    typer.echo(f"MQTT брокер: {broker}")
    typer.echo("")
    
    try:
        # Загружаем конфиг
        cfg = ConfigLoader.load_from_file(config)
        typer.echo(f"Загружено устройств: {len(cfg.devices)}")
        
        # Создаём оркестратор
        _orchestrator = DeviceOrchestrator()
        _orchestrator.load_config(cfg)
        
        # Запускаем асинхронный цикл
        typer.echo("Запуск эмулятора... (нажмите Ctrl+C для остановки)")
        typer.echo("")
        
        asyncio.run(_run_emulator(speed))
        
    except KeyboardInterrupt:
        # asyncio.run() преобразует KeyboardInterrupt в CancelledError,
        # но на всякий случай оставляем обработку
        typer.echo("\n⏹️  Эмулятор остановлен пользователем")
    except Exception as e:
        typer.echo(f"Ошибка: {e}", err=True)
        raise typer.Exit(code=1)


async def _run_emulator(speed: float):
    """Внутренняя асинхронная функция запуска эмулятора"""
    global _orchestrator
    
    # Настройка обработки сигналов для graceful shutdown
    loop = asyncio.get_running_loop()
    
    # Для Windows: SignalHandler работает иначе, используем флаг
    shutdown_requested = False
    
    def signal_handler():
        nonlocal shutdown_requested
        if not shutdown_requested:
            shutdown_requested = True
            typer.echo("\n⏹️  Получен сигнал остановки...")
            asyncio.create_task(_shutdown())
    
    async def _shutdown():
        await _orchestrator.stop_all(graceful=True)
        loop.stop()
    
    # Регистрируем обработчики сигналов (Unix)
    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows не поддерживает add_signal_handler
        # Используем простой флаг
        pass
    
    await _orchestrator.start_all(speed_factor=speed)
    
    # Бесконечный цикл, пока не нажмут Ctrl+C
    try:
        while not shutdown_requested:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    finally:
        if not shutdown_requested:
            await _orchestrator.stop_all(graceful=True)


@app.command()
def stop(
    device_id: Optional[str] = typer.Argument(None, help="ID устройства (если не указан — остановить все)"),
):
    """Остановить устройство или все устройства"""
    global _orchestrator
    
    if _orchestrator is None:
        typer.echo("Эмулятор не запущен", err=True)
        raise typer.Exit(code=1)
    
    async def _stop():
        if device_id:
            success = await _orchestrator.stop_device(device_id)
            if success:
                typer.echo(f"Устройство {device_id} остановлено")
            else:
                typer.echo(f"Устройство {device_id} не найдено", err=True)
        else:
            await _orchestrator.stop_all()
            typer.echo("Все устройства остановлены")
    
    asyncio.run(_stop())


@app.command()
def list_devices():
    """Показать список активных устройств и их статус"""
    global _orchestrator
    
    if _orchestrator is None:
        typer.echo("Эмулятор не запущен", err=True)
        raise typer.Exit(code=1)
    
    statuses = _orchestrator.get_devices_status()
    
    if not statuses:
        typer.echo("Нет активных устройств")
        return
    
    typer.echo(f"\nАктивных устройств: {len(statuses)}")
    typer.echo("-" * 60)
    
    for status in statuses:
        typer.echo(f"  ID: {status['device_id']}")
        typer.echo(f"    Состояние: {'RUNNING' if status['is_running'] else 'STOPPED'}")
        typer.echo(f"    Сообщений отправлено: {status['message_count']}")
        typer.echo(f"    Текущие показания: {status['sensor_values']}")
        typer.echo("")


@app.command()
def inject_error(
    device_id: str = typer.Argument(..., help="ID устройства или 'all'"),
    error_type: str = typer.Option(..., "--error", "-e", help="packet_loss | latency | disconnect"),
    rate: float = typer.Option(0.1, "--rate", "-r", help="Вероятность/интенсивность ошибки (0..1)"),
):
    """Инъекция ошибки в работу устройства"""
    typer.echo(f"⚠️ Инъекция ошибок будет реализована в пункте 9")
    typer.echo(f"   device={device_id}, error={error_type}, rate={rate}")


@app.command()
def replay(
    log_file: str = typer.Argument(..., help="Путь к лог-файлу с телеметрией"),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Коэффициент ускорения воспроизведения"),
    broker: str = typer.Option("localhost:1883", "--broker", "-b", help="MQTT брокер"),
):
    """Воспроизвести телеметрию из лог-файла"""
    typer.echo(f"⚠️ Режим replay будет реализован позже")
    typer.echo(f"   log_file={log_file}, speed={speed}, broker={broker}")


@app.command()
def stats(
    device_id: Optional[str] = typer.Argument(None, help="ID устройства (если не указан — общая статистика)"),
):
    """Показать статистику (количество сообщений, ошибки и т.д.)"""
    global _orchestrator
    
    if _orchestrator is None:
        typer.echo("Эмулятор не запущен", err=True)
        raise typer.Exit(code=1)
    
    if device_id:
        stats_data = _orchestrator.get_device_stats(device_id)
        if stats_data:
            typer.echo(f"\nСтатистика для {device_id}:")
            typer.echo(f"  Сообщений отправлено: {stats_data['message_count']}")
            typer.echo(f"  Состояние: {'RUNNING' if stats_data['is_running'] else 'STOPPED'}")
        else:
            typer.echo(f"Устройство {device_id} не найдено", err=True)
    else:
        statuses = _orchestrator.get_devices_status()
        total_messages = sum(s['message_count'] for s in statuses)
        typer.echo(f"\nОбщая статистика:")
        typer.echo(f"  Активных устройств: {len(statuses)}")
        typer.echo(f"  Всего сообщений: {total_messages}")


def main():
    app()


if __name__ == "__main__":
    main()