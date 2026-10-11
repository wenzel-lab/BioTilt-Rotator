# Power supply design

Options for powering BioTilt inside an incubator, the power budget behind the decision, and the bill of materials for each option.

> **Status:** proposal, pending decision. The prototype currently runs from a **9 V bench supply** and works correctly.
> All power figures below are **estimates** and need to be confirmed by measuring the real input current at ~25 rpm.

---

## 1. Requirements

| Requirement | Value / constraint |
|---|---|
| Runtime | Continuous, up to **~1 week** per experiment |
| Environment | Inside an incubator: ~37 °C, high humidity. **No power outlets inside** |
| Cable | A low-voltage cable through the door seal or access port is acceptable |
| A4988 motor supply (VMOT) | **8–35 V**. A 5 V rail cannot drive it, even though the motor is rated ~4.25 V; the driver limits coil current by chopping |
| Nano ESP32 supply (VIN) | **6–21 V**. The board has its own on-board regulator, so **no external 5 V step-down is needed** |
| Logic (display, pot, A4988 VDD) | 3.3 V from the Nano ESP32 3V3 pin (already the case) |
| Open-source replicability | Parts must be common and work in any country (220 V and 110 V mains) |

---

## 2. Power budget

The A4988 holds a **constant coil current** set by Vref, whatever the speed. Even with 1/16 microstepping, the total coil dissipation stays at about I²·R (the two phase currents follow sin/cos). Power therefore depends on the **current limit**, not on rpm.

Motor: 4.25 V / 1 A per phase → coil resistance R ≈ 4.2 Ω.

| Load | Current limit 0.7 A (current) | Optimised: 0.4 A, display off after timeout |
|---|---|---|
| Motor coils (I²R) | ~2.1 W | ~0.7 W |
| A4988 losses | ~0.3–0.5 W | ~0.15 W |
| Nano ESP32 (Wi-Fi off) | ~0.3 W | ~0.3 W |
| 7-segment display | ~0.1–0.2 W | ~0 W |
| Regulator / converter losses | ~0.4 W | ~0.2 W |
| **Total from the source** | **~3–3.5 W** | **~1.3 W** |
| **Energy for 1 week (168 h)** | **~550 Wh** | **~220 Wh** |

### Firmware improvement (applies to every option)

The driver currently stays enabled (`EN` LOW) when the motor is stopped (0 rpm), so the coils keep dissipating full power. Setting `EN` HIGH at 0 rpm removes that load when the device is idle.

---

## 3. Option A: rechargeable battery (~10 V)

Architecture: 3S Li-ion pack (10.8 V nominal) → BMS / charging module → VMOT + Nano VIN directly (no step-down needed, see §1).

### Battery sizing for one week

| Scenario | Energy | 3S pack capacity | 18650 cells (3 Ah, 3.6 V) | Approx. cell mass |
|---|---|---|---|---|
| Current design | ~550 Wh | ~50 Ah | **3S17P = 51 cells** | ~2.4 kg |
| Optimised stepper (0.4 A, display off) | ~220 Wh | ~20 Ah | **3S7P = 21 cells** | ~1 kg |

### Assessment

- **Not viable for one week** with the current stepper + A4988. The pack would be bigger and heavier than the device.
- A large lithium pack running for days at 37 °C speeds up cell ageing and adds safety risk inside the incubator.
- Charging adds a BMS, a balance charger (3S), and safe charging instructions to the build.
- It only becomes reasonable with a **redesign**:
  - A small geared DC motor instead of the stepper, which draws current only in proportion to load.
  - Intermittent rotation (e.g. 1 min on / 4 min off with the driver disabled between cycles). Note that this **changes the experimental condition** (see [references](../references/README.md)).
- Could still be useful as a **short-term backup** (hours) for transport or power cuts.

---

## 4. Option B: 9 V mains adapter (barrel jack)

Architecture: 220 V wall adapter (outside the incubator) → 9 V DC cable → panel barrel jack → protection → VMOT + Nano VIN.

- This is what the prototype already uses. **It is proven to work.**
- **No step-down module is needed**: the Nano ESP32 takes 9 V on VIN directly.
- 9 V is close to the A4988 minimum (8 V). If a series diode is used for reverse-polarity protection, its drop eats into that margin. Prefer a P-MOSFET, or use a **12 V adapter** for more headroom (both the A4988 and the Nano accept it).
- Mains stays outside the incubator, so the device itself has **no 220 V wiring**.
- Downside: barrel jack size and polarity are not standardised, so users have to source a matching adapter.

---

## 5. Option C (recommended): USB-C Power Delivery at 9 V

Architecture: any USB-C PD charger (outside the incubator) → USB-C cable → panel USB-C connector → **PD trigger module** set to 9 V → protection → VMOT + Nano VIN.

A PD trigger module (based on chips such as CH224K or IP2721) negotiates a fixed voltage with a standard USB-C PD charger.

**Advantages**

- **Universal:** almost every lab and user already has a USB-C PD charger. Any PD charger **≥ 18 W** must offer 9 V under the USB PD spec. Works on 220 V and 110 V.
- **Same electrical setup as option B** (9 V on VMOT + VIN), which is already validated.
- Thin USB-C cables (including flat ones) pass easily through door seals.
- **No mains wiring** in the device, and polarity is guaranteed by the connector, so no reverse-polarity protection is needed.
- A **USB-C PD power bank** can run the device for transport or short power cuts. For example, a 20 000 mAh (~74 Wh) bank gives roughly 20 h at the current consumption.

**Points to check**

- Many PD chargers **do not offer 12 V**. Stay at 9 V, or use 15 V (offered by chargers ≥ 45 W) if more torque at speed is ever needed. Both are within A4988 and Nano limits.
- Choose a trigger module with a **fixed voltage** (solder jumper / resistor). Avoid button-selectable boards, which can reset to 5 V.
- If the charger cannot provide 9 V, the trigger outputs 5 V and the motor will not run. Add a note in the user guide.

---

## 6. Comparison

| Criterion | A. Battery | B. 9 V adapter | C. USB-C PD 9 V |
|---|---|---|---|
| 1-week runtime | ✗ (needs ~50 Ah pack) | ✓ | ✓ |
| Complexity | High (BMS, charger, pack) | Low | Low |
| Extra parts in CAD | Pack + BMS + charge port | Barrel jack | USB-C jack + trigger board |
| Replicability worldwide | Medium | Medium (adapter variety) | **High** |
| Mains inside the device | No | No | No |
| Already tested | No | **Yes** | Same voltage as B |
| Approx. extra cost | High | Low | Low |

**Recommendation:** option C (USB-C PD at 9 V), with option B as a drop-in alternative because the internal circuit is the same. Keep the battery for a possible future low-power version.

---

## 7. Bill of materials: power module

Each option has parts that go **inside the device** (soldered or mounted in the enclosure) and parts that are **external** (plugged in by the user, outside the incubator). The chain is always the same:

**external supply → input module → protection → 9 V rail → A4988 VMOT + Nano ESP32 VIN**

Wiring diagrams for every option, with each module labelled by its ID: **[diagrams/power-supply-diagrams.pdf](diagrams/power-supply-diagrams.pdf)**.

How these parts protect the Nano ESP32 from motor-induced dips, spikes and ground noise, plus the recommended D1/C5 branch and star wiring: **[protections.md](protections.md)**.

### 7.1 Common to all options (inside the device)

| # | Part | Qty | Example / spec | Required | What it does |
|---|---|---|---|---|---|
| P1 | Resettable fuse (PTC polyfuse) | 1 | Hold ~1.1 A, ≥ 16 V (e.g. MF-R110) | Yes | In series with the input. Cuts current on a short circuit and resets by itself |
| P2 | Electrolytic capacitor | 1 | ≥ 100 µF, ≥ 25 V, 105 °C rated | Yes | Across VMOT–GND, right at the A4988. Absorbs large, slow voltage spikes from cable inductance and motor current, which could push VMOT above the A4988's 35 V absolute maximum |
| P3 | Ceramic capacitor | 1 | 100 nF, ≥ 25 V | Optional | In parallel with P2. Filters high-frequency switching noise that the electrolytic is too slow to catch. **Most HW-434 / Pololu-style A4988 boards already include one on VMOT**, so it is usually redundant |
| P4 | TVS diode | 1 | **SMBJ12A** (clamps ~19.9 V, below the Nano's 21 V max; not SMBJ15A) | Recommended | Clamps input surges. See [protections.md](protections.md#33-correctly-rated-tvs-diode) |
| P5 | Power switch | 1 | Panel rocker / slide, ≥ 2 A | Optional (required in option A) | On/off |
| P6 | Wire | – | 22 AWG for power, 26–28 AWG for signals | Yes | |

### 7.2 Option C: USB-C PD (recommended)

The only **module** inside the device is the PD trigger board (C1). It has its own USB-C port and outputs 9 V on two pads (+ / −), which go to P1.

| # | Part | Qty | Example / spec | Where | Required |
|---|---|---|---|---|---|
| C1 | USB-C PD trigger module, fixed voltage | 1 | CH224K- or IP2721-based, set to **9 V** with a jumper/resistor (avoid button-selectable boards) | Inside, at the enclosure wall so its port is reachable | **Yes** |
| C2 | USB-C panel-mount connector (extension) | 1 | Female USB-C, screw or snap-in | Inside, enclosure wall | Optional: only if C1 is mounted away from the wall |
| C3 | USB-C PD charger | 1 | ≥ 18 W, PD 3.0 with 9 V profile | **External**, wall outlet | User supplied |
| C4 | USB-C to USB-C cable | 1 | 2 m, 3 A; flat cable helps at the door seal | **External**, through the door seal | User supplied |

### 7.3 Option B: 9 V adapter

| # | Part | Qty | Example / spec | Where | Required |
|---|---|---|---|---|---|
| B1 | AC/DC wall adapter (with its DC cable) | 1 | 9 V (or 12 V) DC, ≥ 1.5 A, centre-positive, 5.5 × 2.1 mm, certified | **External**, wall outlet | Yes |
| B2 | Panel barrel jack | 1 | 5.5 × 2.1 mm | Inside, enclosure wall | Yes |
| B3 | Reverse-polarity protection | 1 | P-MOSFET (e.g. AO3401A, V_GS ≤ ±12 V, so valid up to 12 V input) + 10 kΩ gate resistor | Inside | Yes. Preferred over a diode: keeps VMOT above 8 V |

### 7.4 Option A: battery (reference only, not recommended for 1 week)

| # | Part | Qty | Example / spec | Where | Required |
|---|---|---|---|---|---|
| A1 | Li-ion cells | 21–51 | 18650, 3 Ah, protected or matched. 3S7P to 3S17P (see §3) | Inside | Yes |
| A2 | 3S BMS with balancing | 1 | ≥ 3 A continuous | Inside | Yes |
| A3 | 3S charger board | 1 | USB-C PD input, 12.6 V CC/CV output | Inside, enclosure wall | Yes |
| A4 | Battery holder / spot-welded pack + enclosure | 1 | Thermal and mechanical protection | Inside | Yes |
| – | USB-C PD charger + cable | 1 | For charging only | **External** | User supplied |

The pack's 9.0–12.6 V range is within both the A4988 (8–35 V) and Nano ESP32 (6–21 V) limits, so this option **does not need a step-down** either.

### 7.5 Test equipment: consumption measurement (not part of the device)

Lab tool for measuring the **real consumption** and confirming the estimates in §2. One unit is enough for the project; it is not built into each BioTilt.

| # | Part | Qty | Example / spec | Where | Required |
|---|---|---|---|---|---|
| T1 | Inline USB-C power meter | 1 | **FNIRSI FNB58** (alternative: ChargerLAB POWER-Z KM003C, higher accuracy and price). Must pass through USB PD negotiation | **External**, between the charger (C3) and the cable (C4), outside the incubator | Yes, for validation |
| S1 | Current sensor module (built in) | 1 | **INA219** (26 V, 0.1 Ω shunt, I²C); alternative INA226 (36 V, higher precision). I²C to Nano **A4 (SDA) / A5 (SCL)**, powered from 3V3 | **Inside**, high side, before the star point (measures motor + Nano) | Optional (future). Allows the firmware to log a time series without a PC |

Placement of T1 and S1: page 5 of [diagrams/power-supply-diagrams.pdf](diagrams/power-supply-diagrams.pdf).

How to use it for a 1-week run:

- Plug it in on the charger side, so it stays outside the incubator.
- Reset one accumulation group to zero before starting. Check the start-current threshold (BioTilt draws ~0.3 A at 9 V).
- The screen shows **live** V / A / W plus **accumulated Wh, mAh and elapsed time**. Average power = Wh ÷ hours.
- The screen does **not** store a time series. To get the consumption curve, keep it connected to a PC (FNIRSI software, CSV export) or to the phone app over Bluetooth for the whole run.
- Check beforehand whether a brief power cut resets the accumulated counter, and photograph the screen at the start and at the end.

---

## 8. Wiring

Full diagrams: **[diagrams/power-supply-diagrams.pdf](diagrams/power-supply-diagrams.pdf)** (page 2: option C, page 3: option B, page 4: option A, page 5: consumption measurement).

Simplified view for options B and C:

```
OUTSIDE                 │ door │  INSIDE THE ENCLOSURE
                        │ seal │
Charger C3 / adapter B1 ═cable═► Input module ─► P1 polyfuse ─► P4 TVS* ─► P5 switch* ─┬─► A4988 VMOT (+ P2, P3*)
                        │      │  C1 trigger, or                                         └─► Nano ESP32 VIN
                        │      │  B2 jack + B3 MOSFET                       * optional      GND common to all
```

- Use **one common ground** for the input, A4988 (both GND pins) and the Nano ESP32.
- Keep VMOT wiring short and thick. Put the capacitors right at the driver.
- Never plug or unplug the motor while powered.

To regenerate the PDF after changes: `python hardware/diagrams/make_power_pdf.py hardware/diagrams/power-supply-diagrams.pdf` (needs `pip install reportlab`).

---

## 9. Next steps

- [ ] Measure the real input current at 9 V (stopped / 25 rpm / 60 rpm) to confirm §2, using the USB-C power meter T1 (§7.5).
- [ ] 1-week run with T1: record total Wh and average power.
- [ ] Decide between option C and option B.
- [ ] Add the connector and trigger board to the CAD enclosure.
- [ ] Firmware: disable the driver (`EN` HIGH) at 0 rpm.
- [ ] Set the A4988 current limit to the lowest value that turns a fully loaded holder reliably.
- [ ] 7-day continuous run inside the incubator: monitor driver/motor temperature.
