# Software

## `firmware/`: ESP32 firmware (PlatformIO)

Target: **Arduino Nano ESP32** (`env:arduino_nano_esp32`).

### Build and flash

1. Install [PlatformIO](https://platformio.org/) (VS Code extension or CLI).
2. Open `software/firmware/` as the project folder.
3. Change `monitor_port` in `platformio.ini` to match your system (e.g. `COM5` on Windows, `/dev/ttyACM0` on Linux).
4. Build and upload: `pio run -t upload`, then open the monitor with `pio device monitor`.

### Behaviour

- **Potentiometer (A0)** sets speed and direction: −60 … +60 rpm, with a ±1 rpm dead zone in the centre (stopped).
- **Serial (115200 baud)**: type an rpm value and press Enter (e.g. `25`, `-25`, `0` to stop). A serial command overrides the pot until the pot is moved again.
- **Display**: shows rpm as `XX.X`. A leading `-` means reverse. `----` means stopped.
- Step generation, pot reading and display refresh are all non-blocking.

### Main parameters (`src/main.cpp`)

| Constant | Default | Meaning |
|---|---|---|
| `MICROSTEPS` | 16 | Must match MS1–MS3 wiring |
| `POT_RPM_MIN` / `POT_RPM_MAX` | −60 / 60 | Speed range (see [references §2.4](../references/README.md#24-practical-speed-bands-synthesis)) |
| `POT_ZONA_MUERTA_RPM` | 1.0 | Dead zone around zero |
| `DIGITO_ACTIVO_EN_ALTO` | false | Set `true` if the digit commons go through NPN transistors |

Pin mapping: see [hardware/README.md §2](../hardware/README.md#2-wiring).
