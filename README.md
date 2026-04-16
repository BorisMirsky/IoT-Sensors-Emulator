# IoT-Sensors-Emulator

Эмулятор IoT-устройств 


### Роль AI в этом проекте
- Примерно три четверти кода сгенерировано DeepSeek, включая структуру проекта и основные маршруты. 
- Почти весь код уточнялся и правился через корректирующие промпты, общим числом более ~50.


### Идея проекта возникла на стыке нескольких источников: 
- проект [Django MQTT IoT Dashboard](https://github.com/matheus-cortejas/Django-MQTT-Test) 
- сценарии поведения через json [SmartLightingSimulation](https://atnog-code.av.it.pt/smartenvironments/smartlightingsimulation/-/blame/a009d21267a69328051be82b0f716cf2fa24eab7/README.md)
- работа через CLI [mqtt-simulator](https://github.com/TheZlodziej/mqtt-simulator)
- курс [Интернет вещей](https://aiu.susu.ru/iot/samsung) от 'Академии Самсунг' 


### Как пользоваться.
- поставить зависимости
- завести виртуальное окружение
- в корне проекта выполнить `python -m iot_emulator start --config configs/test_device.yaml --speed 60`


Эта демо-версия скрипта демонстрирует динамическое изменение поведения устройства по расписанию через JSON-правила, без изменения кода. Температура автоматически растёт, достигает пика, затем падает — всё управляется файлом `temperature_cycle.json`.

Аргументы скрипта:
- Загрузка конфигурации `configs/test_device.yaml` -> создание двух устройств (`test_sensor_1` и `test_sensor_2`)
- `--speed 60` - имитация ускорения времения, цикл смены температур за ~6 реальных секунд

По окончанию проекта будет приложена полная инструкция со всеми вариантами аргументов приложения


