# Foundations

## The Big Three: Voltage, Current, Resistance

- **Voltage (V)** is the potential difference between two points. It is always measured *between* two nodes — there is no such thing as voltage at a single point without an implied reference (usually ground).
- **Current (I)** is the flow of charge through a conductor, measured in amperes. Current flows in loops — it must have a complete path from source through load and back.
- **Resistance (R)** opposes current flow. Ohm's Law: `V = I * R`.

### Ohm's Law — The Most Used Equation

```
V = I * R
I = V / R
R = V / I
```

Every circuit design starts and ends with Ohm's Law. When in doubt, draw the circuit, label the voltages and currents, and apply V = IR.

## Power

```
P = V * I = I^2 * R = V^2 / R
```

**Always check power dissipation.** A resistor that "works" electrically may burn up thermally. Standard through-hole resistors handle 1/4W. SMD 0402s handle 1/16W.

### Quick Power Checks

| Scenario | Formula | Watch for |
|----------|---------|-----------|
| Resistor dropping voltage | P = V_drop^2 / R | Exceeding resistor wattage rating |
| Transistor in linear mode | P = V_CE * I_C | Thermal runaway |
| Voltage regulator | P = (V_in - V_out) * I_load | Regulator overheating |
| LED current-limiting resistor | P = (V_supply - V_LED) * I_LED | Usually fine, but check at high currents |

## Kirchhoff's Laws

### KVL — Kirchhoff's Voltage Law
The sum of voltage drops around any closed loop equals zero. Walk around a loop, adding voltage rises and subtracting drops. They must balance.

**Design use:** When you know the supply voltage and the forward voltage of components in series, KVL tells you what voltage remains for a current-limiting resistor.

Example: 12V supply, 2V LED, need 10mA → R = (12 - 2) / 0.01 = 1kΩ

### KCL — Kirchhoff's Current Law
The sum of currents entering a node equals the sum leaving it. Current doesn't appear or disappear.

**Design use:** When a node drives multiple loads, the source must supply the sum of all load currents.

## Voltage Dividers

```
V_out = V_in * R2 / (R1 + R2)
```

Where R1 connects V_in to V_out, and R2 connects V_out to ground.

### Critical Rule: Voltage Dividers Are Not Power Supplies

A voltage divider only produces a stable voltage if the load current is negligible compared to the divider current. Rule of thumb: **divider current should be at least 10x the load current**.

If your load draws 1mA, the divider must flow at least 10mA. This means low-value resistors and wasted power. For anything beyond biasing or sensing, use a voltage regulator instead.

### Loaded Voltage Divider

When a load R_L is connected to the output:
```
V_out = V_in * (R2 || R_L) / (R1 + R2 || R_L)
```

The output voltage drops. This is why voltage dividers are for sensing, not power delivery.

## Thevenin and Norton Equivalents

Any linear circuit with two terminals can be replaced by:
- **Thevenin:** A voltage source V_th in series with a resistance R_th
- **Norton:** A current source I_n in parallel with a resistance R_n

Where `V_th = I_n * R_n` and `R_th = R_n`.

### How to Find Thevenin Equivalent
1. **V_th**: Open-circuit voltage at the terminals (remove the load)
2. **R_th**: Resistance seen looking back into the terminals with all independent sources turned off (voltage sources → short, current sources → open)

### Why This Matters for Design
- A voltage divider is a Thevenin source with V_th = V_in * R2/(R1+R2) and R_th = R1 || R2
- Source impedance matters: a source with high R_th will sag under load
- Matching impedances maximizes power transfer (but wastes half the power — only do this for RF/audio lines, not power delivery)

## Grounding

Ground is a *reference point*, not a magical current sink. Current flows in loops through real conductors with real impedance.

### Ground Rules
1. **Star ground** for mixed analog/digital: run separate ground traces from each section back to a single point near the power supply
2. **Never assume two "ground" points are at the same voltage** — current through ground traces creates voltage drops (I * R of the trace)
3. **High-current return paths should not share ground traces with sensitive signals**
4. **Bypass capacitors connect between power and ground *at the IC***, not somewhere else on the board

## Units and Prefixes

| Prefix | Symbol | Multiplier | Common Usage |
|--------|--------|------------|--------------|
| pico   | p      | 10^-12     | Capacitors (pF), currents (pA) |
| nano   | n      | 10^-9      | Capacitors (nF), time (ns) |
| micro  | u/μ    | 10^-6      | Capacitors (μF), currents (μA) |
| milli  | m      | 10^-3      | Currents (mA), voltages (mV) |
| kilo   | k      | 10^3       | Resistors (kΩ), frequencies (kHz) |
| mega   | M      | 10^6       | Resistors (MΩ), frequencies (MHz) |
| giga   | G      | 10^9       | Frequencies (GHz) |

**SPICE suffix convention:** In SPICE netlists, use `p`, `n`, `u`, `m`, `k`, `MEG` (not `M` — SPICE reads `M` as milli). `G` for giga, `T` for tera.
