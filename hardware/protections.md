# Electrical protections

How BioTilt protects its electronics, in particular the **Arduino Nano ESP32**, which shares the 9 V supply with the stepper motor driver.

Related documents: [power-supply.md](power-supply.md) (power options and BOM), [diagrams/power-supply-diagrams.pdf](diagrams/power-supply-diagrams.pdf).

---

## 1. What can actually harm the Nano

The motor does not "push" current into the Nano. The Nano only draws what it needs (well under 100 mA). The risk is that the motor **disturbs the voltage** of the 9 V rail they share:

| Problem | Cause | Effect on the Nano |
|---|---|---|
| **Voltage dip** | The A4988 draws current pulses and the cable or supply cannot respond instantly | If deep enough, the ESP32 resets (brownout) |
| **Voltage spike** | Cable inductance when plugging in, or the motor returning energy when it decelerates | Above ~21 V on VIN the Nano can be damaged |
| **Ground noise** | Motor current returns through the same GND wire as the Nano | Erratic potentiometer readings, display flicker, random resets |

---

## 2. Protections already in the design

| Protection | How it helps |
|---|---|
| **A4988 current limit (Vref)** | Motor current is capped by the driver. Unlike a DC motor, a stepper has no large inrush at start-up or stall |
| **Nano on-board regulator** | VIN accepts 6–21 V. A 9 V rail can sag down to ~6 V without affecting the board |
| **P2: 100 µF electrolytic at VMOT** | Supplies the driver's fast current pulses locally, so they barely reach the rail. Also absorbs slow spikes |
| **P1: polyfuse 1.1 A** | Cuts current on a short circuit and resets by itself |
| **Reverse-polarity protection** | Option C: guaranteed by the USB-C connector. Option B: P-MOSFET B3 |

---

## 3. Recommended additions

### 3.1 Star wiring (most important, no cost)

From the output of the fuse/switch, run **separate + and GND wires** to the A4988 and to the Nano. Do not daisy-chain the Nano from the driver's terminals.

```
                     ┌──── + ───► A4988 VMOT (+ P2)
fuse / switch ── ● ──┤
 (star point)        └──── + ───► Nano branch (§3.2)

                     ┌──── GND ─► A4988 GND (motor side)
GND star point ─ ● ──┤
                     └──── GND ─► Nano GND
```

This way motor current never flows through the Nano's wires, which removes most ground noise. The A4988 logic GND and the Nano GND are still connected (they must share a ground for the STEP/DIR/EN signals). Only the **path of the motor current** is kept separate.

### 3.2 Dedicated Nano branch: Schottky diode + capacitor

```
9 V star point ──► D1 (1N5819) ──┬──► Nano VIN
                                 │
                                C5 47–100 µF
                                 │
                                GND
```

- **D1** stops the motor from draining C5 when the rail dips. C5 then keeps the Nano running through short sags.
- Voltage drop ~0.3 V, so VIN is ~8.7 V, well above the 6 V minimum.
- The Nano draws < 100 mA, far below D1's 1 A rating.

### 3.3 Correctly rated TVS diode

A TVS diode clamps voltage spikes on the input. **Its clamping voltage must be below the Nano's 21 V maximum:**

| TVS | Stand-off | Clamping (V_C) | 9 V rail |
|---|---|---|---|
| **SMBJ12A** | 12 V | ~19.9 V | **Correct** |
| SMBJ15A | 15 V | ~24.4 V | **Do not use**: clamps above the Nano's limit |

This is another reason to stay at 9 V. With a 15 V rail, there is no standard TVS that both stays off at 15 V and clamps below 21 V.

### 3.4 Firmware

- The ESP32 has a built-in **brownout detector**. Unexplained resets during operation are a sign of rail dips: check the star wiring and §3.2.
- Disable the driver (`EN` HIGH) at 0 rpm to reduce load and heating (pending, see [power-supply.md §2](power-supply.md#2-power-budget)).

---

## 4. Handling rules

- **Never connect or disconnect the motor while the driver is powered.** The voltage spike destroys the A4988.
- Set Vref **before** running the motor for the first time.
- Check the PD trigger output voltage with a multimeter before connecting it to the circuit. Some configurable modules ship set to 20 V.
- Keep VMOT wires short and thick. Mount P2 right at the driver pins.

---

## 5. Protection BOM

| # | Part | Qty | Example / spec | Status |
|---|---|---|---|---|
| P1 | Polyfuse | 1 | Hold ~1.1 A, ≥ 16 V (MF-R110) | Required |
| P2 | Electrolytic capacitor | 1 | ≥ 100 µF, ≥ 25 V, 105 °C | Required |
| P3 | Ceramic capacitor | 1 | 100 nF, ≥ 25 V | Optional (usually already on the A4988 board) |
| P4 | TVS diode | 1 | **SMBJ12A** (9 V rail) | Recommended |
| D1 | Schottky diode | 1 | 1N5819 (1 A, 40 V) | Recommended |
| C5 | Electrolytic capacitor | 1 | 47–100 µF, ≥ 25 V, 105 °C | Recommended |
| B3 | P-MOSFET + 10 kΩ | 1 | AO3401A | Option B only |
