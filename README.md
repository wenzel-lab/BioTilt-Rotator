# BioTilt-Rotator
Compact, incubator-compatible tube rotator for microbiology. Inclined rotation keeps cultures mixed without inverting open tubes. Gentle, continuous motion supports growth and aeration with minimal disturbance. Open-source design for easy fabrication and customization.

## Repository layout

| Folder | Contents |
|---|---|
| [`hardware/`](hardware/README.md) | Bill of materials, wiring, assembly manual, diagrams |
| [`software/`](software/README.md) | ESP32 firmware (PlatformIO) |
| [`documents/`](documents/README.md) | Datasheets, validation experiments, user guide |
| [`references/`](references/README.md) | Commercial devices and literature on rotation speed and its effect on cultures |

## Quick facts (prototype)

- Arduino Nano ESP32 + A4988 + NEMA 17 stepper
- 0–60 rpm, both directions, set with a potentiometer or over serial
- 4-digit 7-segment display showing rpm
- Power supply: under design
