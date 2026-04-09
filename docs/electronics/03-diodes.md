# Diodes and LEDs

## Diode Fundamentals

A diode conducts in one direction. Forward-biased: current flows, voltage drop is ~0.6V (silicon) or ~0.3V (Schottky). Reverse-biased: no current flows (until breakdown).

### The Diode Equation (Simplified)

```
I = Is * (e^(V / (n * Vt)) - 1)
```

Where Vt ≈ 26mV at room temperature, Is is the saturation current (typically pA to nA), and n is the ideality factor (1–2).

**For design purposes, just use the forward voltage drop from the datasheet.** The exponential relationship means the voltage is nearly constant over a wide range of currents.

### Forward Voltage Drops (Typical)

| Diode Type | V_f (typical) | Notes |
|------------|---------------|-------|
| Silicon (1N4148) | 0.6–0.7V | General purpose signal diode |
| Silicon rectifier (1N4001) | 0.7–1.0V | Higher at high currents |
| Schottky (1N5819) | 0.2–0.4V | Lower drop, good for power |
| Germanium | 0.2–0.3V | Obsolete, fragile, temperature-sensitive |
| Red LED | 1.8–2.2V | Varies by manufacturer |
| Green LED | 2.0–2.2V | Standard green, not "pure" green |
| Blue/White LED | 3.0–3.6V | Higher voltage = more sensitive to current |
| Zener (various) | Rated value | Operates in reverse breakdown |

## LED Drive Circuits

### Basic LED Circuit: Resistor Current Limiting

The simplest and most common way to drive an LED:

```
R = (V_supply - V_LED) / I_LED
```

**Typical LED currents:** 
- Standard indicator LED: 10–20mA (often fine at 5–10mA for indicators)
- High-brightness LED: 20mA at rated current
- Power LED: 350mA–1A+ (requires constant-current driver)

**Example:** 5V supply, red LED (V_f = 2.0V), desired 10mA:
```
R = (5 - 2.0) / 0.010 = 300Ω → use 330Ω (nearest E12 value)
Actual current = 3.0V / 330Ω = 9.1mA (close enough)
Power in resistor = 3.0V * 9.1mA = 27mW (fine for 1/4W resistor)
```

### LED Current from Logic Outputs

Most logic gates and microcontroller pins can source or sink 10–20mA. Check the datasheet for I_OH (source) and I_OL (sink) specifications.

**Sinking is usually stronger than sourcing.** Connect the LED from V+ through a resistor to the output pin, and drive the pin LOW to turn the LED ON.

```
V+ ──[ R ]──|>|── MCU pin (active low)
```

### Driving LEDs from Higher Voltage Sources

When V_supply >> V_LED, the resistor wastes significant power. For automotive (12V) or industrial (24V) applications:

- At 12V with a 2V LED at 20mA: R = 500Ω, P = 200mW — acceptable
- At 24V with a 2V LED at 20mA: R = 1.1kΩ, P = 440mW — consider a constant-current source
- For multiple LEDs: wire them in series to use more of the supply voltage across LEDs and less across the resistor

### Constant-Current LED Drive

For stable brightness regardless of supply voltage variations, use a constant-current source:

**Simple 2-transistor current source:**
```
V+ ──[ R_sense ]──┬── LED ──┬── GND
                   │         │
                   Q1(C)   Q2(E)
                   Q1(B)───Q2(C)
                   Q1(E)───GND
                   Q2(B)───junction of R_sense and LED
```

Or use a dedicated constant-current LED driver IC for power LEDs.

### LED Series Strings

To drive multiple LEDs efficiently:
- Wire LEDs in series — they share the same current, no matching needed
- Total V_f = sum of individual V_f values
- V_supply must exceed total V_f by enough for the current-limiting element
- **Never wire LEDs in parallel** without individual current limiting resistors — V_f mismatch causes current hogging

## Zener Diode Voltage Regulators

A Zener diode in reverse bias maintains approximately constant voltage across it.

### Basic Zener Regulator
```
V_in ──[ R_series ]──┬── V_out
                      │
                     [Zener]
                      │
                     GND
```

```
R_series = (V_in - V_zener) / (I_zener + I_load)
```

### Zener Regulator Limitations

**Zener regulators are terrible voltage regulators.** Use them only for:
- Reference voltages at very low current (<5mA)
- Voltage clamping/protection
- Biasing in circuits where precision doesn't matter

Problems:
- **Load regulation is poor** — output voltage changes with load current
- **V_z varies with temperature** — Zeners below 5V have negative tempco, above 5V positive. At ~5.6V, the tempco crosses zero.
- **They waste power** — R_series must be sized for worst case (max V_in, min I_load), so at nominal conditions there's excess current through the Zener
- **Noise** — Zener breakdown is inherently noisy (especially above 5V where avalanche breakdown dominates)

For any serious voltage regulation, use a three-terminal regulator IC (see [Power](08-power.md)).

## Protection Diodes

### Reverse Polarity Protection
Place a diode in series with the power input. Simple but wastes V_f in voltage drop. Better: use a P-channel MOSFET for near-zero drop.

### Flyback/Freewheeling Diodes
**Every inductive load (relay, motor, solenoid) MUST have a flyback diode.** When current through an inductor is interrupted, it generates a voltage spike (V = L * dI/dt) that will destroy transistors.

```
         ┌──|<|──┐
V+ ──────┤       ├── Switch to GND
         │ RELAY  │
         └────────┘
```

The diode is reverse-biased during normal operation and conducts only during the inductive kick, clamping the spike to one diode drop.

**Use a fast diode** (1N4148 for small relays, 1N4001 for larger ones, or a Schottky for fastest clamping).

### ESD Protection
Clamp diodes to the supply rails protect inputs from electrostatic discharge:
```
V+ ──|<|── INPUT ──|>|── GND
```

Many ICs have these built in, but external TVS diodes are needed for connectors exposed to the outside world.

## SPICE Modeling Notes

### Simple Diode Model
For basic SPICE simulations, a diode model needs at minimum:
```
.model D_NAME D (IS=value N=value RS=value BV=value IBV=value)
```

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| IS | Saturation current | 1e-14 (silicon), 1e-8 (Schottky) |
| N | Ideality factor | 1.0–2.0 |
| RS | Series resistance | 0.5–10Ω |
| BV | Reverse breakdown voltage | 100V (rectifier), 5.1V (Zener) |
| IBV | Current at breakdown | 100μA (Zener) |

### LED Model
```
.model LED_RED D (IS=1e-20 N=1.8 RS=5 BV=5 IBV=100u)
```
The high ideality factor (N=1.8) and low IS give a forward voltage around 1.8–2.0V at 10–20mA. Adjust N and IS to match the desired V_f.

| LED Color | IS | N | Approximate V_f |
|-----------|----|---|-----------------|
| Red | 1e-20 | 1.8 | 1.8–2.0V |
| Green | 1e-22 | 2.0 | 2.0–2.2V |
| Blue/White | 1e-30 | 2.5 | 3.0–3.4V |
