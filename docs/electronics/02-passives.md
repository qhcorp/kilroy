# Resistors and Passive Components

## Resistors

### Standard Values (E-Series)

Resistors come in preferred value series. You cannot buy arbitrary values. Design with standard values.

- **E12 (10% tolerance):** 10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82 — then multiply by decades (100, 120, ... 8.2k, 10k, 12k, ...)
- **E24 (5% tolerance):** Adds 11, 13, 16, 20, 24, 30, 36, 43, 51, 62, 75, 91
- **E96 (1% tolerance):** Fine-grained, but use only when precision matters

**Design rule:** Choose the nearest standard value. If the nearest value doesn't work, you have a fragile design — add a trimmer or change the topology.

### Resistor Types and When They Matter

| Type | Use Case | Avoid When |
|------|----------|------------|
| Carbon film | General purpose, cheap | Precision or low-noise needed |
| Metal film | Precision, low noise, tight tolerance | Never — these are the default choice |
| Wirewound | High power (5W+), current sensing | High frequency (they're inductive) |
| Thick film SMD | General SMD, most applications | Precision below 0.1% |
| Thin film SMD | Precision SMD | Cost is the only concern |

### Power Derating

Resistors must be derated at elevated temperatures. **Never run a resistor at more than 50% of its rated power** in a real design. At 70°C ambient, most resistors are already derated to ~60% of their rating.

### Parasitic Properties

All resistors have parasitic capacitance (~0.5pF) and inductance (~10nH for through-hole). This matters above 10MHz. At high frequencies, a 1MΩ resistor behaves like a capacitor.

**Rule of thumb:** Keep resistor values between 100Ω and 100kΩ for active circuits. Below 100Ω wastes power. Above 100kΩ picks up noise and is affected by parasitic capacitance.

## Capacitors

### Capacitor Types — Choose Correctly

| Type | Range | Characteristics | Use For |
|------|-------|-----------------|---------|
| Ceramic (C0G/NP0) | 1pF–10nF | Stable, precise, low loss | Timing, filters, precision |
| Ceramic (X7R) | 100pF–10μF | ±15% variation with voltage and temp | Bypass, coupling, general |
| Ceramic (Y5V) | 1nF–100μF | Loses 80% capacitance at rated voltage | Almost nothing — avoid |
| Electrolytic (aluminum) | 1μF–10,000μF | Polarized, high ESR, limited life | Bulk filtering, power supply |
| Electrolytic (tantalum) | 100nF–1000μF | Polarized, lower ESR, can fail short | Bulk filtering where size matters |
| Film (polyester/polypropylene) | 1nF–10μF | Stable, low loss, large | Audio, precision timing, snubbers |

### Critical: Ceramic Capacitor Voltage Derating

X7R and X5R ceramic capacitors **lose significant capacitance when DC bias is applied**. A "10μF" 0402 X5R capacitor rated at 6.3V may have only 2μF of actual capacitance at 5V bias.

**Rule:** For X7R/X5R, use a voltage rating at least 2x your operating voltage, or check the manufacturer's voltage derating curve.

### Bypass Capacitor Rules

1. **Every IC gets a 100nF ceramic capacitor between V+ and GND**, placed as close to the IC pins as physically possible
2. For ICs drawing >100mA, add a 10μF electrolytic/tantalum nearby
3. For precision analog ICs, use 100nF || 10μF (two caps in parallel — the ceramic handles high-frequency noise, the electrolytic handles low-frequency)
4. **The return path matters as much as the capacitor** — a bypass cap on a long trace is nearly useless

### ESR (Equivalent Series Resistance)

Real capacitors have resistance in series with the ideal capacitance. This matters for:
- **Power supply filtering:** High-ESR electrolytics can't suppress high-frequency switching noise
- **Timing circuits:** ESR adds a real component that affects RC time constants
- **Output capacitors on voltage regulators:** Some regulators *require* a minimum ESR for stability (check the datasheet)

## Inductors

### Inductor Properties

Inductors resist *changes* in current: `V = L * dI/dt`. They store energy in magnetic fields: `E = 0.5 * L * I^2`.

### Key Parameters
- **Inductance (L):** In henries. Most circuit inductors are μH to mH range.
- **DCR (DC resistance):** Real inductors have winding resistance. This wastes power and drops voltage.
- **Saturation current:** The current at which inductance drops (typically by 20-30%). **Never exceed this.**
- **SRF (Self-Resonant Frequency):** Above this, the inductor acts like a capacitor. Use well below SRF.

### Inductor Applications
| Application | Typical Range | Key Concern |
|-------------|---------------|-------------|
| Switching power supply | 1μH–100μH | Saturation current, DCR, core losses |
| EMI filtering | 10μH–10mH | Impedance at noise frequency |
| RF matching | 1nH–100nH | Q factor, SRF |
| Energy storage | 100μH–10mH | Saturation current |

## Practical Component Selection Rules

1. **Use standard values.** Don't design circuits that require exact non-standard resistor values.
2. **Derate everything.** Capacitor voltage 2x, resistor power 2x, transistor current 2x.
3. **Minimize the number of unique component values.** Fewer unique parts = simpler BOM = cheaper.
4. **Check availability.** A perfect design is useless if the part is obsolete or has a 52-week lead time.
5. **Temperature matters.** Check that components are rated for your operating range. Consumer is 0–70°C, industrial is -40 to +85°C, automotive is -40 to +125°C.
