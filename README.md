
# IoT Device Emulator

Эмулятор IoT-устройств на Python с поддержкой MQTT, симуляцией датчиков, сценариями поведения и инъекцией ошибок.

## Возможности

- Симуляция нескольких устройств с независимыми датчиками
- Реалистичные датчики с инерцией, шумом и корреляцией (температура, влажность, бинарный, счётчик)
- Симуляция времени с коэффициентом ускорения (60x = 1 минута за 1 секунду)
- MQTT — каждое устройство имеет свой клиент, публикует телеметрию в реальном времени
- Сценарии поведения — динамическое изменение целевых значений по расписанию (JSON-правила)
- Инъекция ошибок — потеря пакетов, задержки, отключения устройств
- Логирование телеметрии в JSON Lines + возможность воспроизведения (replay)
- Корректная остановка всех устройств по Ctrl+C

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/iot-device-emulator.git
cd iot-device-emulator
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

Активация:

- **Windows (cmd)**: `venv\Scripts\activate.bat`
- **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`
- **Linux / MacOS**: `source venv/bin/activate`

### 3. Установка зависимостей

```bash
pip install -e .
```

### 4. Проверка установки

```bash
python -m iot_emulator --help
```


## Быстрый старт

### 1. Создайте файл конфигурации устройства (configs/my_devices.yaml)

```yaml
devices:
  - id: living_room
    mqtt:
      broker: localhost:1883
      telemetry_topic: "home/living_room/sensors"
    sensors:
      - type: temperature
        initial: 22.5
        noise_std: 0.3
      - type: humidity
        initial: 55.0
        noise_std: 2.0
    publish_interval: 5.0
```

### 2. Запустите эмулятор

```bash
python -m iot_emulator start --config configs/my_devices.yaml --speed 60
```

### 3. Наблюдайте за телеметрией в консоли

```text
[14:30:01.123] [living_room] TELEMETRY: {'temperature': 22.5, 'humidity': 55.0}
[14:30:06.456] [living_room] TELEMETRY: {'temperature': 22.7, 'humidity': 54.8}
```

### 4. Остановите эмулятор нажатием Ctrl+C

## Интерфейс командной строки (CLI)

### Глобальные команды

| Команда | Сокращение | Аргументы | Пример | Описание |
|---------|------------|-----------|--------|----------|
| `start` | - | `--config` (обяз), `--speed`, `--broker` | `python -m iot_emulator start -c config.yaml -s 60` | Запуск эмулятора с конфигурацией |
| `stop` | - | `[device_id]` | `python -m iot_emulator stop living_room` | Остановка конкретного устройства или всех |
| `list-devices` | - | - | `python -m iot_emulator list-devices` | Показать активные устройства и их статус |
| `stats` | - | `[device_id]` | `python -m iot_emulator stats living_room` | Показать статистику сообщений |
| `inject-error` | - | `device_id`, `--error`, `--rate`, `--duration` | `python -m iot_emulator inject-error all --error packet_loss --rate 0.3` | Инъекция сетевых ошибок |
| `replay` | - | `log_file`, `--speed`, `--broker` | `python -m iot_emulator replay logs/telemetry.jsonl --speed 10` | Воспроизведение телеметрии из лог-файла |


### Аргументы команды `start`

| Аргумент | Сокращение | Тип | По умолчанию | Описание |
|----------|------------|-----|--------------|----------|
| `--config` | `-c` | строка | **обязательный** | Путь к YAML файлу конфигурации |
| `--speed` | `-s` | число | 1.0 | Коэффициент ускорения времени (60 = 1 реальная секунда = 1 симулированная минута) |
| `--broker` | `-b` | строка | localhost:1883 | Адрес MQTT брокера (host:port) |



### Аргументы команды `inject-error`

| Аргумент | Сокращение | Тип | По умолчанию | Описание |
|----------|------------|-----|--------------|----------|
| `device_id` | - | строка | **обязательный** | ID устройства или "all" |
| `--error` | `-e` | строка | **обязательный** | Тип ошибки: `packet_loss`, `latency`, `disconnect` |
| `--rate` | `-r` | число | 0.1 | Вероятность ошибки (0.0 - 1.0) |
| `--duration` | `-d` | число | 5.0 | Длительность отключения в секундах (для ошибки `disconnect`) |
| `--min-delay` | - | число | 0.5 | Минимальная задержка в секундах (для ошибки `latency`) |
| `--max-delay` | - | число | 3.0 | Максимальная задержка в секундах (для ошибки `latency`) |
| `--remove` | - | флаг | False | Удалить ошибку вместо добавления |


## Конфигурация

### Структура YAML

```yaml
devices:
  - id: unique_device_id                    # Обязательно, уникальный идентификатор
    mqtt:
      broker: "localhost:1883"              # Необязательно, по умолчанию: localhost:1883
      telemetry_topic: "sensors/device1"    # Обязательно
      qos: 0                                # Необязательно, по умолчанию: 0
    sensors:                                # Обязательно, хотя бы один
      - type: temperature                   # Обязательно: temperature | humidity | binary | counter
        initial: 22.5                       # Необязательно, значение по умолчанию зависит от датчика
        noise_std: 0.3                      # Необязательно, по умолчанию: 0
        min_value: -10                      # Необязательно (для temperature, humidity)
        max_value: 50                       # Необязательно (для temperature, humidity)
    behavior_script: "behaviors/cycle.json" # Необязательно, путь к JSON сценарию поведения
    publish_interval: 5.0                   # Необязательно, по умолчанию: 5.0 секунд
```


### Типы датчиков

| Тип | Описание | Специфические параметры |
|-----|----------|--------------------------|
| `temperature` | Температура с инерцией | `inertia` (0.1 по умолчанию), `min_value`, `max_value` |
| `humidity` | Влажность, может коррелировать с температурой | `correlation_with` (имя датчика) |
| `binary` | Бинарное состояние (0/1) | `toggle_probability` (0.001 по умолчанию) |
| `counter` | Монотонный счётчик | `increment_rate` (0.01 по умолчанию) |

### Сценарий поведения (JSON)

Пример `behaviors/temperature_cycle.json`:

```json
{
    "rules": [
        {
            "type": "set_target",
            "condition": {"simulated_time": "> 30"},
            "action": {"sensor": "temperature", "value": 25.0}
        },
        {
            "type": "publish_alert",
            "condition": {"sensor": {"sensor": "temperature", "operator": ">", "value": 27}},
            "action": {"message": "Высокая температура!"}
        }
    ]
}
```


**Типы правил:**
- `set_target` — изменение целевого значения датчика
- `add_offset` — добавление смещения к текущему значению датчика
- `publish_alert` — вывод предупреждения в лог
- `change_interval` — динамическое изменение интервала публикации

**Условия:**
- `{"simulated_time": "> 60"}` — по времени
- `{"sensor": {"sensor": "temperature", "operator": ">", "value": 30}}` — по значению датчика
- `{"command": "heater_on"}` — по команде (MQTT)


### Пример 1: Два устройства с разными датчиками

```yaml
devices:
  - id: sensor_kitchen
    mqtt:
      telemetry_topic: "home/kitchen/sensors"
    sensors:
      - type: temperature
        initial: 23.0
        noise_std: 0.5
      - type: humidity
        initial: 60.0
        noise_std: 3.0
    publish_interval: 3.0

  - id: sensor_garage
    mqtt:
      telemetry_topic: "home/garage/sensors"
    sensors:
      - type: binary
        name: door_open
        initial: 0
    publish_interval: 1.0
```

### Пример 2: Запуск с ускорением и логированием телеметрии

```bash
python -m iot_emulator start --config configs/home.yaml --speed 120
```

### Пример 3: Инъекция потери пакетов на всех устройствах

```bash
python -m iot_emulator inject-error all --error packet_loss --rate 0.5
```


### Пример 4: Воспроизведение телеметрии из лог-файла

```bash
python -m iot_emulator replay logs/telemetry_20250115_203001.jsonl --speed 10
```

## Структура проекта

```text
iot-device-emulator/
├── src/iot_emulator/
│   ├── cli/              # Команды Typer CLI
│   ├── core/             # Устройство, Оркестратор
│   ├── sensors/          # Температура, Влажность, Бинарный, Счётчик
│   ├── mqtt/             # Обёртка MQTT клиента
│   ├── behavior/         # Парсер JSON правил
│   ├── errors/           # Потеря пакетов, задержки, отключения
│   ├── time_simulation/  # Контроллер симулированного времени
│   └── logging/          # Логгер телеметрии в JSON Lines
├── configs/              # YAML конфигурации устройств
├── logs/                 # Логи телеметрии (создаются при запуске)
├── tests/                # Модульные и интеграционные тесты
├── pyproject.toml        # Зависимости и метаданные пакета
└── README.md
```

## Источники вдохновения:

- [архитектура - 1](https://github.com/mqtt-smarthome/mqtt-smarthome)
- [архитектура - 2](https://github.com/matheus-cortejas/Django-MQTT-Test) 
- [сценарии поведения через json](https://atnog-code.av.it.pt/smartenvironments/smartlightingsimulation/-/blame/a009d21267a69328051be82b0f716cf2fa24eab7/README.md)
- [идеи CLI аргументов и логирования](https://github.com/TheZlodziej/mqtt-simulator)
- [курс 'Интернет вещей' от 'Академии Самсунг'](https://aiu.susu.ru/iot/samsung) 


## Ситуации для применения данного проекта

### 1. Тестирование MQTT-инфраструктуры без реальных устройств

Предположим, у нас есть система мониторинга умного дома. Нужно проверить, как система обрабатывает поток данных от `n` датчиков температуры и влажности.

Результат: Нашли баги в обработке данных до того, как купили реальные датчики.


### 2. Нагрузочное тестирование MQTT-брокера

Хотим узнать, выдержит ли выбранный MQTT-брокер `n` одновременно подключённых устройств, публикующих данные `m` раз в секунду.

Результат: Выясняли, что брокер падает при, например, `n - 200` устройствах.


### 3.  Воспроизведение инцидентов

Предположим, что система мониторинга показала аномалию и воспроизвести ситуацию вручную невозможно.

Результат: Воспроизвели инцидент, нашли баг в коде обработчика.


### 4. Тестирование отказоустойчивости 

Проверка работы системы при нестабильной сети.

Результат: Нашли, что при потере пакетов обработчик, условно, падает с KeyError.


### 5. Демонстрация

Нужно наглядно показать, как MQTT-устройства публикуют данные, а система их обрабатывает.

Зритель (заказчик) понимает, как работает система.


### Ограничения (когда эмулятор НЕ подходит)

- Тестирование прошивки устройств — эмулятор не заменяет реальную плату с датчиками.

- Задержки реального мира — симуляция времени не эмулирует физическую инерцию проводов.

- Некорректные MQTT-клиенты — эмулятор использует корректную реализацию paho-mqtt.

- Сетевые протоколы кроме MQTT — эмулятор не поддерживает CoAP, LwM2M, Modbus.
