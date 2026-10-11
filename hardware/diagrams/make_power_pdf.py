import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle

OUT = sys.argv[1]
W, H = landscape(A4)

RED = colors.HexColor("#c62828")
BLK = colors.HexColor("#222222")
BLUE = colors.HexColor("#1565c0")
GREY = colors.HexColor("#666666")
FILL = {
    "external": colors.HexColor("#eeeeee"),
    "input": colors.HexColor("#dbe9f7"),
    "protect": colors.HexColor("#fff3c4"),
    "load": colors.HexColor("#d9f0dc"),
    "battery": colors.HexColor("#f6dcdc"),
    "measure": colors.HexColor("#e6dcf5"),
}

cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=7.3, leading=8.8)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=8)


class Block:
    def __init__(self, x, y, w, h, tag, title, lines, kind, optional=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.tag, self.title, self.lines, self.kind, self.optional = tag, title, lines, kind, optional

    @property
    def cy(self):
        return self.y + self.h / 2

    @property
    def right(self):
        return self.x + self.w


def draw_block(c, b):
    c.setFillColor(FILL[b.kind])
    c.setStrokeColor(GREY if b.optional else BLK)
    c.setLineWidth(1)
    c.setDash(3, 2) if b.optional else c.setDash()
    c.roundRect(b.x, b.y, b.w, b.h, 5, fill=1, stroke=1)
    c.setDash()
    # tag badge
    if b.tag:
        tw = c.stringWidth(b.tag, "Helvetica-Bold", 7.5) + 8
        c.setFillColor(BLK)
        c.roundRect(b.x + 4, b.y + b.h - 13, tw, 10, 2, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(b.x + 8, b.y + b.h - 10.5, b.tag)
    if b.optional:
        c.setFillColor(GREY)
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawRightString(b.right - 4, b.y + b.h - 10.5, "optional")
    c.setFillColor(BLK)
    c.setFont("Helvetica-Bold", 8)
    ty = b.y + b.h - 25
    for t in b.title.split("\n"):
        c.drawCentredString(b.x + b.w / 2, ty, t)
        ty -= 9.5
    c.setFont("Helvetica", 6.8)
    c.setFillColor(colors.HexColor("#333333"))
    for t in b.lines:
        c.drawCentredString(b.x + b.w / 2, ty, t)
        ty -= 8.3


def wire(c, pts, color, width=1.6):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke=1, fill=0)


def hop_h(c, x1, x2, y, hop_x, color):
    """Horizontal wire from x1 to x2 that hops over a vertical wire at hop_x."""
    r = 4
    wire(c, [(x1, y), (hop_x - r, y)], color)
    c.setStrokeColor(color)
    c.arc(hop_x - r, y - r, hop_x + r, y + r, 0, 180)
    wire(c, [(hop_x + r, y), (x2, y)], color)


def pair(c, a, b, label=None):
    """+ and GND wires between two blocks in a row."""
    wire(c, [(a.right, a.cy + 7), (b.x, b.cy + 7)], RED)
    wire(c, [(a.right, a.cy - 7), (b.x, b.cy - 7)], BLK)
    if label:
        c.setFont("Helvetica", 6.3)
        c.setFillColor(GREY)
        c.drawCentredString((a.right + b.x) / 2, a.cy + 11, label)


def dot(c, x, y, color):
    c.setFillColor(color)
    c.circle(x, y, 2.2, fill=1, stroke=0)


def zones(c, y0, y1, outside_label="OUTSIDE THE INCUBATOR", seal_x=222):
    c.setFillColor(colors.HexColor("#f7f7f7"))
    c.rect(22, y0, seal_x - 30, y1 - y0, fill=1, stroke=0)
    c.setFillColor(GREY)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(28, y1 - 11, outside_label)
    # door seal / port
    c.setFillColor(colors.HexColor("#9e9e9e"))
    c.rect(seal_x - 4, y0, 8, y1 - y0, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 6.8)
    c.setFillColor(GREY)
    c.drawCentredString(seal_x, y1 + 4, "Door seal / access port")
    # enclosure
    c.setStrokeColor(BLK)
    c.setDash(6, 3)
    c.setLineWidth(1)
    c.rect(234, y0, W - 234 - 22, y1 - y0, fill=0, stroke=1)
    c.setDash()
    c.setFillColor(BLK)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(240, y1 - 11, "BIOTILT ENCLOSURE (inside the incubator, ~37 °C)")


def loads(c, from_block, rail_label):
    """Common load: A4988 + Nano ESP32, fed from a + / GND bus."""
    a = Block(672, 330, 140, 82, "", "A4988 driver (HW-434)",
              ["VMOT / GND  (8-35 V)", "P2 100 µF + P3 100 nF* at VMOT", "1A 1B 2A 2B -> NEMA 17 motor"], "load")
    n = Block(672, 196, 140, 76, "", "Arduino Nano ESP32",
              ["VIN / GND  (6-21 V)", "on-board regulator -> 3.3 V", "3V3 -> A4988 VDD, pot, display"], "load")
    draw_block(c, a)
    draw_block(c, n)
    xp, xg = 640, 652
    yp, yg = from_block.cy + 7, from_block.cy - 7
    wire(c, [(from_block.right, yp), (xp, yp)], RED)
    wire(c, [(from_block.right, yg), (xg, yg)], BLK)
    # buses
    wire(c, [(xp, n.cy + 7), (xp, a.cy + 7)], RED)
    wire(c, [(xg, n.cy - 7), (xg, a.cy - 7)], BLK)
    dot(c, xp, yp, RED)
    dot(c, xg, yg, BLK)
    wire(c, [(xp, a.cy + 7), (a.x, a.cy + 7)], RED)
    hop_h(c, xp, n.x, n.cy + 7, xg, RED)
    wire(c, [(xg, a.cy - 7), (a.x, a.cy - 7)], BLK)
    wire(c, [(xg, n.cy - 7), (n.x, n.cy - 7)], BLK)
    # signals
    sx = a.x + a.w / 2
    wire(c, [(sx, n.y + n.h), (sx, a.y)], BLUE, 1.2)
    c.setFont("Helvetica", 6.5)
    c.setFillColor(BLUE)
    c.drawRightString(sx - 4, (n.y + n.h + a.y) / 2 - 2, "STEP D2 / DIR D3 / EN D4")
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(xp - 4, a.cy + 4, rail_label)
    return a, n


def header(c, title, subtitle):
    c.setFillColor(BLK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, H - 42, title)
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawString(30, H - 58, subtitle)
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(30, H - 66, W - 30, H - 66)


def footer(c, n):
    c.setFont("Helvetica", 7)
    c.setFillColor(GREY)
    c.drawString(30, 16, "BioTilt-Rotator · hardware/diagrams/power-supply-diagrams.pdf · see hardware/power-supply.md")
    c.drawRightString(W - 30, 16, f"Page {n}")


def parts_table(c, rows, y_top):
    data = [[Paragraph(h, cellb) for h in ["ID", "Part", "What it does", "Where", "Required"]]]
    for r in rows:
        data.append([Paragraph(str(v), cell) for v in r])
    t = Table(data, colWidths=[34, 170, 360, 120, 98])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    tw, th = t.wrapOn(c, W - 60, 300)
    t.drawOn(c, 30, y_top - th)


def chain(c, blocks):
    for b in blocks:
        draw_block(c, b)
    for a, b in zip(blocks, blocks[1:]):
        pair(c, a, b)


def outlet(c):
    b = Block(30, 228, 72, 62, "", "Wall outlet", ["220 V / 110 V AC"], "external")
    draw_block(c, b)
    return b


# ---------------------------------------------------------------- page 1
c = canvas.Canvas(OUT, pagesize=landscape(A4))
c.setTitle("BioTilt power supply diagrams")
c.setAuthor("BioTilt-Rotator project")

header(c, "BioTilt - Power supply wiring diagrams",
       "Block diagrams for the three power options in hardware/power-supply.md. Option C is the recommended one.")

y = H - 95
c.setFont("Helvetica-Bold", 11)
c.setFillColor(BLK)
c.drawString(30, y, "Contents")
c.setFont("Helvetica", 9.5)
for i, t in enumerate(["Page 2 - Option C: USB-C Power Delivery at 9 V (recommended)",
                       "Page 3 - Option B: 9 V mains adapter with barrel jack",
                       "Page 4 - Option A: rechargeable 3S Li-ion battery (reference only)",
                       "Page 5 - Consumption measurement: USB-C power meter (T1) and optional INA219 sensor (S1)"]):
    c.drawString(40, y - 16 - 14 * i, t)

# legend
ly = y - 85
c.setFont("Helvetica-Bold", 11)
c.drawString(30, ly, "Legend")
legend = [("external", False, "Outside the device: supplied by the user (charger, adapter, cable)"),
          ("input", False, "Input module: where power enters the enclosure"),
          ("protect", False, "Protection / switching"),
          ("protect", True, "Dashed border = optional part"),
          ("battery", False, "Battery-related part (option A only)"),
          ("load", False, "BioTilt electronics (same in every option)"),
          ("measure", False, "Consumption measurement (page 5)")]
for i, (k, opt, txt) in enumerate(legend):
    yy = ly - 22 - 18 * i
    c.setFillColor(FILL[k])
    c.setStrokeColor(GREY if opt else BLK)
    c.setDash(3, 2) if opt else c.setDash()
    c.roundRect(40, yy - 4, 26, 13, 3, fill=1, stroke=1)
    c.setDash()
    c.setFillColor(BLK)
    c.setFont("Helvetica", 9)
    c.drawString(76, yy, txt)

wy = ly - 22 - 18 * len(legend) - 6
for i, (col, txt) in enumerate([(RED, "+ supply (9 V rail)"), (BLK, "GND (common ground)"), (BLUE, "Logic signals")]):
    wire(c, [(40, wy - 16 * i + 3), (66, wy - 16 * i + 3)], col, 2.5)
    c.setFillColor(BLK)
    c.drawString(76, wy - 16 * i, txt)
c.setFont("Helvetica", 8.5)
c.drawString(40, wy - 52, "Crossing wires with a hop are NOT connected. A dot marks a junction.")

# key points (right column)
from reportlab.platypus import Frame
notes = [
    "<b>Key points</b>",
    "<b>No 5 V step-down is needed.</b> The Arduino Nano ESP32 accepts 6-21 V on VIN and has its own "
    "regulator. The same 9 V rail feeds the A4988 VMOT (8-35 V) and the Nano VIN. This is how the "
    "prototype already runs from a 9 V supply.",
    "<b>Mains (220 V) never enters the device.</b> In options B and C the charger/adapter stays outside "
    "the incubator and only a low-voltage cable passes the door seal.",
    "<b>Capacitors at VMOT.</b> P2 (100 µF electrolytic) absorbs slow, large voltage spikes from cable "
    "inductance and motor current, and protects the A4988 from going over 35 V. P3 (100 nF ceramic) "
    "filters high-frequency switching noise. *Most HW-434 / Pololu-style boards already include a ceramic "
    "capacitor on VMOT, so P3 is optional.",
    "<b>Common ground.</b> The input GND, both A4988 GND pins and the Nano GND must be connected together.",
    "<b>Never connect or disconnect the motor while the driver is powered.</b>",
]
f = Frame(470, 60, W - 500, H - 150, showBoundary=0)
f.addFromList([Paragraph(t, body) for t in notes], c)
footer(c, 1)
c.showPage()

# ---------------------------------------------------------------- page 2: option C
header(c, "Option C - USB-C Power Delivery at 9 V  (recommended)",
       "Any USB-C PD charger >= 18 W offers 9 V. Inside the device there is only ONE input module: the PD trigger board (C1).")
Y0, Y1 = 180, 480
zones(c, Y0, Y1)
o = outlet(c)
ch = Block(112, 222, 92, 74, "C3", "USB-C PD\ncharger", [">= 18 W, PD 3.0", "user supplied"], "external")
draw_block(c, ch)
c1 = Block(250, 222, 100, 74, "C1", "USB-C PD trigger", ["CH224K / IP2721", "fixed 9 V (jumper)", "has its own USB-C port"], "input")
p1 = Block(368, 230, 76, 58, "P1", "Polyfuse", ["1.1 A hold"], "protect")
p4 = Block(460, 230, 76, 58, "P4", "TVS diode", ["SMBJ12A", "recommended"], "protect")
p5 = Block(552, 230, 76, 58, "P5", "Power switch", [">= 2 A"], "protect", optional=True)
# AC wiring
wire(c, [(o.right, o.cy + 5), (ch.x, o.cy + 5)], GREY)
wire(c, [(o.right, o.cy - 5), (ch.x, o.cy - 5)], GREY)
# USB-C cable crossing the seal
c.setStrokeColor(colors.HexColor("#5d4037"))
c.setLineWidth(4)
c.line(ch.right, ch.cy, c1.x, c1.cy)
c.setFont("Helvetica-Bold", 7)
c.setFillColor(colors.HexColor("#5d4037"))
c.drawString(30, ch.y - 14, "C4: USB-C cable to C1 (2 m, 3 A, flat)")
chain(c, [c1, p1, p4, p5])
loads(c, p5, "+9 V")
# C2 note
c2 = Block(250, 330, 100, 56, "C2", "USB-C panel jack", ["only if C1 is not at", "the enclosure wall"], "input", optional=True)
draw_block(c, c2)
c.setStrokeColor(GREY)
c.setDash(2, 2)
c.setLineWidth(0.8)
c.line(c2.x + c2.w / 2, c2.y, c1.x + c1.w / 2, c1.y + c1.h)
c.setDash()

parts_table(c, [
    ["C3", "USB-C PD charger", "Converts mains to USB-C; negotiates 9 V with C1", "Outside (wall)", "Yes (user supplied)"],
    ["C4", "USB-C to USB-C cable", "Carries 9 V through the door seal", "Through the seal", "Yes (user supplied)"],
    ["C1", "USB-C PD trigger module", "Asks the charger for 9 V and outputs it on + / - pads. <b>The only module in the device.</b>", "Enclosure wall", "Yes"],
    ["C2", "USB-C panel connector", "Extension so the port sits on the wall if C1 is mounted further inside", "Enclosure wall", "Optional"],
    ["P1", "Polyfuse 1.1 A", "Cuts current on a short circuit, resets by itself", "Enclosure", "Yes"],
    ["P4", "TVS diode SMBJ12A", "Clamps input spikes below the Nano 21 V limit (see protections.md)", "Enclosure", "Recommended"],
    ["P5", "Power switch", "On/off", "Enclosure wall", "Optional"],
    ["P2 / P3", "100 µF / 100 nF capacitors", "Stabilise VMOT at the A4988 (see page 1)", "At the A4988", "P2 yes, P3 optional"],
], 168)
footer(c, 2)
c.showPage()

# ---------------------------------------------------------------- page 3: option B
header(c, "Option B - 9 V mains adapter (barrel jack)",
       "This is how the prototype runs today. Same 9 V rail as option C. Only the input module changes.")
zones(c, Y0, Y1)
o = outlet(c)
ad = Block(112, 222, 92, 74, "B1", "AC/DC adapter", ["9 V (or 12 V) DC", ">= 1.5 A, certified", "centre-positive"], "external")
draw_block(c, ad)
b2 = Block(248, 230, 70, 58, "B2", "Barrel jack", ["5.5 x 2.1 mm", "panel mount"], "input")
b3 = Block(332, 230, 80, 58, "B3", "Reverse-polarity", ["P-MOSFET AO3401A", "+ 10 kohm gate res."], "protect")
p1 = Block(426, 230, 64, 58, "P1", "Polyfuse", ["1.1 A hold"], "protect")
p4 = Block(504, 230, 56, 58, "P4", "TVS", ["SMBJ12A", "recommended"], "protect")
p5 = Block(572, 230, 56, 58, "P5", "Switch", [">= 2 A"], "protect", optional=True)
wire(c, [(o.right, o.cy + 5), (ad.x, o.cy + 5)], GREY)
wire(c, [(o.right, o.cy - 5), (ad.x, o.cy - 5)], GREY)
c.setStrokeColor(colors.HexColor("#5d4037"))
c.setLineWidth(4)
c.line(ad.right, ad.cy, b2.x, b2.cy)
c.setFont("Helvetica-Bold", 7)
c.setFillColor(colors.HexColor("#5d4037"))
c.drawString(30, ad.y - 14, "DC cable of B1 to the barrel jack B2")
chain(c, [b2, b3, p1, p4, p5])
loads(c, p5, "+9 V")
parts_table(c, [
    ["B1", "AC/DC wall adapter 9 V", "Converts mains to 9 V DC. Use 12 V for more margin above the A4988 8 V minimum", "Outside (wall)", "Yes"],
    ["B2", "Panel barrel jack 5.5 x 2.1 mm", "Input connector on the enclosure wall", "Enclosure wall", "Yes"],
    ["B3", "P-MOSFET (AO3401A) + 10 kohm", "Blocks current if the adapter has the wrong polarity. Drops much less voltage than a diode, which keeps VMOT above 8 V. Gate rating allows inputs up to 12 V", "Enclosure", "Yes"],
    ["P1", "Polyfuse 1.1 A", "Cuts current on a short circuit, resets by itself", "Enclosure", "Yes"],
    ["P4", "TVS diode SMBJ12A", "Clamps input spikes below the Nano 21 V limit (see protections.md)", "Enclosure", "Recommended"],
    ["P5", "Power switch", "On/off", "Enclosure wall", "Optional"],
    ["P2 / P3", "100 µF / 100 nF capacitors", "Stabilise VMOT at the A4988 (see page 1)", "At the A4988", "P2 yes, P3 optional"],
], 168)
footer(c, 3)
c.showPage()

# ---------------------------------------------------------------- page 4: option A
header(c, "Option A - Rechargeable 3S Li-ion battery  (reference only)",
       "Not recommended for 1-week runs: ~550 Wh needed with the current motor (3S17P, ~51 cells). See power-supply.md section 3.")
zones(c, Y0, Y1, outside_label="OUTSIDE (only while charging)")
o = outlet(c)
chg = Block(112, 222, 92, 74, "", "USB-C PD\ncharger", ["for charging only", "user supplied"], "external")
draw_block(c, chg)
a3 = Block(248, 222, 92, 74, "A3", "3S charger board", ["USB-C PD input", "12.6 V CC/CV out"], "battery")
a2 = Block(362, 222, 92, 74, "A2", "3S BMS", ["balancing", ">= 3 A continuous", "P+ / P- output"], "battery")
a1 = Block(362, 360, 92, 70, "A1", "Battery pack 3S", ["18650, 3S7P - 3S17P", "9.0 - 12.6 V"], "battery")
p1 = Block(476, 230, 66, 58, "P1", "Polyfuse", ["1.1 A hold"], "protect")
p5 = Block(560, 230, 66, 58, "P5", "Switch", ["needed to", "stop drain"], "protect")
wire(c, [(o.right, o.cy + 5), (chg.x, o.cy + 5)], GREY)
wire(c, [(o.right, o.cy - 5), (chg.x, o.cy - 5)], GREY)
c.setStrokeColor(colors.HexColor("#5d4037"))
c.setLineWidth(4)
c.line(chg.right, chg.cy, a3.x, a3.cy)
c.setFont("Helvetica-Bold", 7)
c.setFillColor(colors.HexColor("#5d4037"))
c.drawString(30, chg.y - 14, "USB-C cable to A3 (only while charging)")
chain(c, [a3, a2, p1, p5])
draw_block(c, a1)
# pack <-> BMS
wire(c, [(a2.x + 30, a2.y + a2.h), (a1.x + 30, a1.y)], RED)
wire(c, [(a2.x + 62, a2.y + a2.h), (a1.x + 62, a1.y)], BLK)
c.setFont("Helvetica", 6.5)
c.setFillColor(GREY)
c.drawString(a2.right + 4, (a2.y + a2.h + a1.y) / 2 - 2, "B+ / B- (+ balance leads)")
loads(c, p5, "+9.0-12.6 V")
parts_table(c, [
    ["A1", "Li-ion pack 3S (18650)", "Stores energy. 3S = 10.8 V nominal, 9.0-12.6 V range: within A4988 and Nano limits, so <b>no step-down is needed</b>", "Enclosure", "Yes"],
    ["A2", "3S BMS with balancing", "Protects cells (over/under-voltage, over-current) and balances them", "Enclosure", "Yes"],
    ["A3", "3S charger board (USB-C PD in)", "Charges the pack at 12.6 V CC/CV from a USB-C charger", "Enclosure wall", "Yes"],
    ["P1", "Polyfuse 1.1 A", "Short-circuit protection on the load side", "Enclosure", "Yes"],
    ["P5", "Power switch", "Disconnects the load so the pack does not drain in storage", "Enclosure wall", "Yes"],
    ["P2 / P3", "100 µF / 100 nF capacitors", "Stabilise VMOT at the A4988 (see page 1)", "At the A4988", "P2 yes, P3 optional"],
], 168)
footer(c, 4)
c.showPage()
# ---------------------------------------------------------------- page 5: consumption measurement
header(c, "Consumption measurement  (shown on option C)",
       "T1 measures the real total consumption from outside, with no changes to the device. S1 is an optional internal sensor for logging from the firmware.")
zones(c, Y0, Y1)
o = Block(28, 222, 54, 74, "", "Wall\noutlet", ["220 / 110 V"], "external")
draw_block(c, o)
ch = Block(88, 222, 58, 74, "C3", "USB-C\nPD", ["charger", ">= 18 W"], "external")
draw_block(c, ch)
t1 = Block(152, 222, 60, 74, "T1", "USB-C\nmeter", ["FNIRSI FNB58", "V, A, W, Wh"], "measure")
draw_block(c, t1)
c1 = Block(248, 230, 76, 58, "C1", "PD trigger", ["fixed 9 V"], "input")
p1 = Block(336, 230, 62, 58, "P1", "Polyfuse", ["1.1 A hold"], "protect")
p4 = Block(410, 230, 62, 58, "P4", "TVS", ["SMBJ12A"], "protect")
p5 = Block(484, 230, 58, 58, "P5", "Switch", [">= 2 A"], "protect", optional=True)
s1 = Block(554, 222, 76, 74, "S1", "INA219", ["current sensor", "high side,", "0.1 ohm shunt"], "measure", optional=True)
wire(c, [(o.right, o.cy + 5), (ch.x, o.cy + 5)], GREY)
wire(c, [(o.right, o.cy - 5), (ch.x, o.cy - 5)], GREY)
c.setStrokeColor(colors.HexColor("#5d4037"))
c.setLineWidth(4)
c.line(ch.right, ch.cy, t1.x, t1.cy)
c.line(t1.right, t1.cy, c1.x, c1.cy)
c.setFont("Helvetica-Bold", 7)
c.setFillColor(colors.HexColor("#5d4037"))
c.drawString(30, ch.y - 14, "C4: USB-C cable from T1 to C1")
chain(c, [c1, p1, p4, p5, s1])
a, n = loads(c, s1, "+9 V")
# I2C from S1 to the Nano
ix = s1.x + s1.w / 2
wire(c, [(ix, s1.y), (ix, 204), (n.x, 204)], BLUE, 1.2)
c.setFont("Helvetica", 6.5)
c.setFillColor(BLUE)
c.drawString(ix - 60, 192, "I2C: SDA -> A4, SCL -> A5 (VCC 3V3, GND)")
# annotation for T1
c.setFont("Helvetica-Oblique", 6.5)
c.setFillColor(colors.HexColor("#5e35b1"))
c.drawString(30, t1.y + t1.h + 24, "T1 stays outside the incubator,")
c.drawString(30, t1.y + t1.h + 15, "on the charger side.")
c.drawString(30, t1.y + t1.h + 6, "Measures everything after the charger.")

parts_table(c, [
    ["T1", "Inline USB-C power meter (FNIRSI FNB58; alt. POWER-Z KM003C)",
     "Shows live V / A / W plus accumulated Wh, mAh and time. Average power = Wh / hours. The screen does NOT store a time series: for a curve, keep it connected to a PC (CSV export) or the phone app for the whole run. Must pass PD negotiation through",
     "External, between C3 and C4", "Yes, for validation (one per project)"],
    ["S1", "INA219 current sensor module (alt. INA226 for 36 V / higher precision)",
     "Measures V, A and W of the 9 V rail and sends them to the Nano over I2C (A4/A5, the pins left free for I2C). Placed before the star point it measures the TOTAL (motor + Nano). The firmware can log a time series (Serial, flash or microSD) without a PC",
     "Inside, before the star point", "Optional (future)"],
    ["-", "What to expect",
     "The A4988 holds coil current almost constant, so consumption will be nearly flat (~0.3 A at 9 V estimated). Useful to confirm the power budget and detect faults (motor disconnected, wrong voltage). It does NOT detect a stalled motor",
     "-", "-"],
], 168)
footer(c, 5)
c.showPage()
c.save()
print("ok", OUT)
