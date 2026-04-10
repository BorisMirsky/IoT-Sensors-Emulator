# Импортируем первым, чтобы настроить логирование до всего остального
import iot_emulator  # noqa: F401

from iot_emulator.cli.app import main

if __name__ == "__main__":
    main()