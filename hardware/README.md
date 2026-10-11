# Hardware

How to build the BioTilt tube rotator.

- [`diagrams/`](diagrams/): wiring diagram *(pending, to be added)*
- [`power-supply.md`](power-supply.md): power options, power budget and power-module BOM
- [`protections.md`](protections.md): how the Nano and driver are protected (TVS, star wiring, diode branch)
- CAD (Onshape): <https://cad.onshape.com/documents/fe4a458ada6fdcda58b4d6de/w/e2fc6b1bc5d415547321a480/e/4297323c847362b5a099e030>

> **Status:** prototype. Power supply design is **not final yet** (see [§4](#4-power-supply-tbd)).

---

## 1. Bill of materials (prototype)

| # | Part | Qty | Notes |
|---|---|---|---|
| 1 | Arduino Nano ESP32 | 1 | 3.3 V logic, **not 5 V tolerant** |
| 2 | A4988 stepper driver on HW-434 carrier board | 1 | MS1/MS2/MS3 tied HIGH → 1/16 microstepping |
| 3 | NEMA 17 stepper motor (200 steps/rev) | 1 | Rated ~4.25 V / 1 A per phase (check your motor's label) |
| 4 | Potentiometer, 10 kΩ linear | 1 | Speed + direction control. *May be replaced by a rotary encoder for the open-source release (needs to be a commonly available part)* |
| 5 | 4-digit 7-segment display, common cathode | 1 | Shows rpm as `XX.X`, `-` = reverse direction, `----` = stopped |
| 6 | Resistors 220–330 Ω | 8 | Segment current limiting (a–g + dp) |
| 7 | *(Recommended)* NPN transistors 2N2222 / BC337 + 1 kΩ base resistors | 4 | Drive the digit commons (see §3.3) |
| 8 | Electrolytic capacitor ≥ 100 µF | 1 | Across VMOT–GND, close to the A4988 |
| 9 | Power supply | 1 | **TBD**: proposal is a USB-C PD charger + 9 V trigger module (see [power-supply.md](power-supply.md#7-bill-of-materials-power-module)). Prototype uses a 9 V supply |
| 10 | Tube holder / tilted frame | 1 | Onshape design |
| 11 | Wires, perfboard or PCB, enclosure | – | Enclosure must tolerate incubator conditions (≈ 37 °C, high humidity) |

---

## 2. Wiring

The final diagram will go in [`diagrams/`](diagrams/). Until then, this table is the reference. It matches [`software/firmware/src/main.cpp`](../software/firmware/src/main.cpp).

### 2.1 Stepper driver (A4988)

| A4988 pin | Connects to |
|---|---|
| STEP | Nano ESP32 **D2** |
| DIR | Nano ESP32 **D3** |
| ENABLE | Nano ESP32 **D4** (active LOW) |
| MS1, MS2, MS3 | 3.3 V (1/16 microstepping) |
| RESET, SLEEP | Bridged together to 3.3 V |
| VDD | 3.3 V (Nano ESP32 3V3 pin) |
| GND (logic) | GND |
| VMOT / GND (motor) | Motor supply (**TBD**, §4) + 100 µF capacitor |
| 1A, 1B, 2A, 2B | Stepper coils (coil pairs: check with a multimeter) |

### 2.2 Potentiometer

| Pot pin | Connects to |
|---|---|
| End 1 | 3.3 V |
| Wiper | **A0** |
| End 2 | GND |

Centre position = stopped (±1 rpm dead zone). Turning either way sets the speed, up to **±60 rpm**, and the direction.

### 2.3 7-segment display

| Signal | Nano ESP32 pin | Signal | Nano ESP32 pin |
|---|---|---|---|
| Seg a | D5 | Seg g | D11 |
| Seg b | D6 | Seg dp | D12 |
| Seg c | D7 | Digit 1 | D13 |
| Seg d | D8 | Digit 2 | A1 |
| Seg e | D9 | Digit 3 | A2 |
| Seg f | D10 | Digit 4 | A3 |

Each segment line goes through a 220–330 Ω resistor. A4/A5 are left free for future I²C use.

---

## 3. Assembly manual

> Draft. Photos and step-by-step figures will be added as the prototype is finalised.

### 3.1 Mechanical

1. Print or fabricate the frame and tube holder from the Onshape design.
2. Mount the NEMA 17 on the inclined bracket. **Record the tilt angle.** It affects the culture (see [references §2.3](../references/README.md#23-low-speed-low-shear-rotation-changes-physiology-not-just-growth)).
3. Attach the tube holder to the motor shaft. Check that it turns freely and that tubes cannot slide out at the chosen angle.

### 3.2 Electronics

1. **Set the A4988 current limit before connecting the motor.** With the driver powered, measure Vref (between the trim-pot and GND) and set it to `Vref = I_max × 8 × R_sense`. HW-434/A4988 boards usually have R_sense = 0.1 Ω or 0.068 Ω (read the resistors marked `R100` / `R068`). For a 1 A motor that gives Vref ≈ 0.8 V or 0.54 V. Running ~70 % of rated current keeps the motor cooler inside the incubator.
2. Wire the driver following §2.1. Solder the 100 µF capacitor right at VMOT/GND.
3. Wire the potentiometer (§2.2) and the display (§2.3).
4. **Never connect or disconnect the motor while the driver is powered.** That destroys the A4988.

### 3.3 Display: note on digit current

In the current prototype the digit commons go **directly** to GPIOs (`DIGITO_ACTIVO_EN_ALTO = false` in the firmware). With "8." lit, one pin has to sink the current of all 8 segments, which can go over the ESP32-S3's recommended ~20 mA per pin. For a robust build, drive each common through an NPN transistor (GPIO → 1 kΩ → base, collector → common, emitter → GND) and set `DIGITO_ACTIVO_EN_ALTO = true`.

### 3.4 Firmware

See [`software/`](../software/README.md).

### 3.5 First power-up checklist

- [ ] Vref set, motor connected **before** power is applied
- [ ] Pot centred: display shows `----`, motor holds still
- [ ] Turn pot: rpm shows on the display, motor turns, direction changes when you cross the centre
- [ ] Driver and motor temperature after 30 min at the target rpm (incubators are already at 37 °C)

---

## 4. Power supply (TBD)

Full analysis, power budget and BOM: **[power-supply.md](power-supply.md)**. The prototype runs correctly from 9 V into both VMOT and the Nano ESP32 VIN.

Still under discussion. Options being considered:

- Low-voltage DC cable fed into the incubator (incubators have no internal outlet).
- Battery pack with USB-C charging (not viable for 1-week runs with the current motor; see power-supply.md §3).
- USB-C PD charger + 9 V trigger module (recommended).

Constraints that any option has to meet:

- **The A4988 needs VMOT between 8 and 35 V.** It cannot run the motor from a 5 V rail, even if the motor is rated at ~4.25 V. The driver limits coil current by chopping, so a higher supply voltage is normal and expected.
- The Nano ESP32 needs 5 V (USB) or 6–21 V on VIN.
- Average current depends on the current-limit setting, not the speed. Budget ~0.5–1 A from the motor supply when holding or turning.
