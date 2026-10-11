# References

Background for choosing BioTilt's operating range (speed, tilt angle, fill volume).
It has two parts:

1. **Commercial devices**: what comparable rotators offer and where on each product page the information is.
2. **Scientific literature**: papers that support (or put limits on) the choice of rotation speed and mixing intensity.

> Last reviewed: 2026-10-09. Product pages change often. If a link breaks, search the catalogue number. All DOIs checked against Crossref.

---

## 1. Commercial devices

### 1.1 Genesee Scientific: Digital Tube Rotator, Large Capacity (Cat. 27-543)

- Link: <https://geneseesci.com/shop-online/product-details/27-543>
- **"Technical Specifications"** section:
  - Speed: **5–80 rpm**, ±1 rpm accuracy (some versions of the page say 2–80 rpm).
  - Tilt angle, adjustable in six steps: **95°, 112°, 129°, 146°, 163°, 180°**.
  - Timer up to 99 h 59 min.
  - Capacity: 15 × 50 mL, 30 × 15 mL, 20 × 5/7 mL, or 64 culture tubes (14 or 18.5 mm). Carousel Ø 290 mm.
  - Operating environment: **5–40 °C, < 80 % RH**. Rated for cold rooms and incubators.
- **"Detailed Description"** section: "gentle circular rotating motion" for clinical, research and teaching labs.
- **Takeaway for BioTilt:** a commercial rotator for culture tubes covers about 5–80 rpm, and the tilt angle is a user setting, not a fixed value. Our firmware range (±60 rpm) sits inside that window.

### 1.2 Boekel Scientific: Rotators

- Link: <https://www.boekelsci.com/products/rockers-rotators-shakers.html/rotators/>
- **"Mini Tube Rotator"**: 360° rotation, 36 × 1.5–2 mL tubes (optional carousels for 10–15 mL or 50 mL). Rated for cold rooms and incubators. Molecular biology and histochemistry uses. No speed given on the overview page.
- **"Tube Rotator"**: "90-degree end-over-end mixing or 180-degree centrifugal mixing with a **tilting head**". Digital speed control described as going from "gentle to vigorous". 14 × 50 mL.
- **Takeaway for BioTilt:** commercial vendors treat the tilting head as the feature that switches between end-over-end mixing (tube inverts) and gentle rotation (tube stays inclined and does not invert). BioTilt does the second one, which is what lets it run **open or loosely capped tubes**.

### 1.3 Labnet / LSPI: I5110A-MLR Mini Incubator + Mini LabRoller combo

- Links: <https://www.e-lspi.com> (original), and the reseller listing <https://www.tequipment.net/Labnet-International/I5110A-MLR-230E/Incubators-and-Ovens>
- Specifications (product description):
  - Rotisserie at a **fixed 24 rpm**.
  - Incubator 5–60 °C, 9.2 L chamber.
  - Rotisseries included for 1.5 mL, 15 mL and 50 mL tubes.
- **Takeaway for BioTilt:** this is the closest commercial product to our use case (a rotator inside a small incubator). The manufacturer judged one fixed speed of about **24 rpm** to be enough for general incubated mixing.

### 1.4 Open-source reference design

- Dhankani K.C. & Pearce J.M. (2016). *Open source laboratory sample rotator mixer and shaker.* **HardwareX** 1:1–12. <https://doi.org/10.1016/j.ohx.2016.07.001>
  - 3D-printed, battery-powered rotator that runs in any orientation from horizontal to vertical. Uses a **12 V geared DC motor at 60 rpm**. Built for under US$30.
  - The paper explicitly targets **incubators, cold rooms and hoods**, which is the same use case as ours. It is a good template for the documentation format (BOM, build steps, validation).

### Summary table

| Device | Speed | Angle | Notes |
|---|---|---|---|
| Genesee 27-543 | 5–80 rpm | 95–180° (6 steps) | Incubator-safe, 5–40 °C, < 80 % RH |
| Boekel Tube Rotator | adjustable ("gentle → vigorous") | tilting head | 90° end-over-end or 180° |
| Labnet I5110A-MLR | 24 rpm fixed | fixed | Rotator inside a mini incubator |
| Dhankani & Pearce 2016 (open source) | 60 rpm fixed (motor) | any, 0–90° | Battery, < US$30 |
| **BioTilt (current firmware)** | **0–60 rpm, both directions** | fixed incline (TBD) | NEMA 17 + A4988, 1/16 µstep |

---

## 2. What rotation speed does, according to the literature

There is very little published work on **inclined tube rotators** in particular. Most of the quantitative literature is on orbital shake flasks and microplates. The physical principles carry over, though: more agitation gives more gas–liquid surface renewal, more oxygen transfer and more shear. Below, each paper is listed with the claim it supports.

### 2.1 Why mix at all: oxygen does not diffuse into a static culture fast enough

- **Somerville G.A. & Proctor R.A. (2013).** *Cultivation conditions and the diffusion of oxygen into culture media: the rationale for the flask-to-medium ratio in microbiology.* **BMC Microbiology** 13:9. <https://doi.org/10.1186/1471-2180-13-9>
  - Oxygen does not diffuse readily into culture medium. Aeration in batch culture depends on **vessel-to-medium ratio, agitation speed (rpm) and baffles**, and these have to be set empirically for each application.
  - Example in the main text (final section): with *Staphylococcus epidermidis* at 160 rpm, going from a 7:1 to a 4:1 vessel:medium ratio switches its metabolism from acetate to **lactate** (a sign of oxygen limitation) and increases biofilm matrix.
  - **Relevance:** report rpm, tube volume and fill volume in every BioTilt experiment. Lower speed or a fuller tube can push a culture toward microaerobic metabolism.

- **Juergensmeyer M.A., Nelson E.S. & Juergensmeyer E.A. (2007).** *Shaking alone, without concurrent aeration, affects the growth characteristics of Escherichia coli.* **Letters in Applied Microbiology** 45(2):179–183. <https://doi.org/10.1111/j.1472-765X.2007.02172.x>
  - Agitated *E. coli* cultures in rigid containers left lag phase **earlier** and reached **higher final OD** than static controls, **even without extra access to air**.
  - **Relevance:** mixing alone (nutrient homogenisation, keeping cells in suspension) helps growth, apart from any oxygen benefit. This supports gentle rotation at low rpm.

### 2.2 More agitation means more oxygen transfer, and rich media need a lot of it

- **Losen M., Frölich B., Pohl M. & Büchs J. (2004).** *Effect of oxygen limitation and medium composition on Escherichia coli fermentation in shake-flask cultures.* **Biotechnology Progress** 20(4):1062–1068. <https://doi.org/10.1021/bp034282t>
  - Online oxygen-transfer-rate (OTR) measurements showed that standard shake-flask conditions **often do not support unlimited growth**. In **Terrific Broth**, cultures were **oxygen-limited below ~400 rpm** (orbital shaker).
  - **Relevance:** a slow rotator (tens of rpm) will **not** match an orbital shaker for dense, aerobic, rich-medium cultures. BioTilt is meant for **gentle mixing**, not for maximum-OTR cultivation, and the documentation should say so.

- **Büchs J. (2001).** *Introduction to advantages and problems of shaken cultures.* **Biochemical Engineering Journal** 7(2):91–98. <https://doi.org/10.1016/S1369-703X(00)00106-6>
  - Review: OTR rises with shaking frequency, shaking diameter and lower fill volume. It also covers the "out-of-phase" phenomenon in viscous cultures.

- **Duetz W.A. et al. (2000).** *Methods for intense aeration, growth, storage, and replication of bacterial strains in microtiter plates.* **Applied and Environmental Microbiology** 66(6):2641–2646. <https://doi.org/10.1128/AEM.66.6.2641-2646.2000>
  - Maximum OTR of ~38 mmol L⁻¹ h⁻¹ (kLa ≈ 188 h⁻¹) at **300 rpm, 5 cm throw, 0.5 mL**. This is a useful upper benchmark for small-volume vessels.

- **Running J.A. & Bansal K. (2016).** *Oxygen transfer rates in shaken culture vessels from Fernbach flasks to microtiter plates.* **Biotechnology and Bioengineering** 113(8):1729–1735. <https://doi.org/10.1002/bit.25938>
  - Reported OTR ranges from about 5 mmol L⁻¹ h⁻¹ (unbaffled Fernbach, 200 rpm) to 140 mmol L⁻¹ h⁻¹ (250 mL Ultra Yield flask, 300 rpm, 50 mm throw). Shows how much vessel geometry matters, on the same order as rpm.

### 2.3 Low speed, low shear: rotation changes physiology, not just growth

- **Nickerson C.A. et al. (2000).** *Microgravity as a novel environmental signal affecting Salmonella enterica serovar Typhimurium virulence.* **Infection and Immunity** 68(6):3147–3152. <https://doi.org/10.1128/IAI.68.6.3147-3152.2000>
  - *Materials and Methods → "Bacterial strains and growth conditions"*: HARV rotating-wall vessel at **25 rpm**, horizontal axis (low-shear modelled microgravity) vs **vertical axis (control)**.
  - The horizontally rotated cultures showed **higher virulence** in mice, more acid-stress resistance and changed protein expression.
  - **Relevance:** at **~25 rpm**, the axis orientation alone changes the fluid-shear regime enough to change bacterial phenotype. The tilt angle is therefore an **experimental variable**, not just a mechanical detail. Keep it fixed and report it.

- **Crabbé A. et al. (2008).** *Use of the rotating wall vessel technology to study the effect of shear stress on growth behaviour of Pseudomonas aeruginosa PA01.* **Environmental Microbiology** 10(8):2098–2110. <https://doi.org/10.1111/j.1462-2920.2008.01631.x>
  - Low-shear rotation caused *P. aeruginosa* to form **self-aggregating suspended biofilms** and upregulated **rhl quorum sensing** and the **psl** polysaccharide locus. Adding a bead to raise shear brought back surface-attached biofilm.
  - **Relevance:** in species that form biofilms, slow rotation can promote aggregation. Faster rotation, or a higher-shear tube geometry, favours dispersed growth.

### 2.4 Practical speed bands (synthesis)

These are **guidelines drawn from the sources above**, not validated BioTilt values. They have to be checked experimentally (growth curves / OD₆₀₀ against a static and a shaken control).

| Range | Expected effect | Typical use | Support |
|---|---|---|---|
| 0 rpm (static) | Cells sediment; O₂ gradient; microaerobic at the bottom | Anaerobes / microaerophiles, controls | Somerville & Proctor 2013 |
| **~5–15 rpm** | Gentle resuspension, very low shear; small O₂ gain | Shear-sensitive cells, keeping sediments in suspension, long incubations | Genesee lower range; Juergensmeyer 2007 |
| **~20–30 rpm** | Homogeneous suspension, low-shear regime; possible aggregation in biofilm-forming species | **General default for incubated tubes** | Labnet 24 rpm; Nickerson 2000 (25 rpm); Crabbé 2008 |
| **~40–60 rpm** | Stronger surface renewal, better O₂ transfer; more meniscus movement (splash risk with open tubes) | Aerobic cultures at moderate density | Dhankani & Pearce 2016 (60 rpm); Genesee upper range |
| > 80 rpm | Outside the rotator category; at high density an orbital shaker (≥ 200 rpm) is still needed | Not a BioTilt target | Losen et al. 2004; Büchs 2001 |

**What this means for BioTilt:**
- The ±60 rpm firmware range covers the useful window. Consider **~25 rpm as the documented default**.
- Report **tilt angle, tube type, fill volume and rpm** in every experiment (Somerville & Proctor 2013).
- Validation still to do: growth curves of a reference strain (e.g. *E. coli* MG1655 in LB) at 0 / 10 / 25 / 50 rpm, plus a 200 rpm orbital-shaker control.

---

## Other links from the project discussion

- Onshape CAD (Tobias Wenzel): <https://cad.onshape.com/documents/fe4a458ada6fdcda58b4d6de/w/e2fc6b1bc5d415547321a480/e/4297323c847362b5a099e030>
- Project repository: <https://github.com/wenzel-lab/BioTilt-Rotator>
