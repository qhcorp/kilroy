# Precision and Low-Noise Design

## Noise Sources

Every electronic component generates noise. Understanding the sources lets you minimize their impact.

### Thermal Noise (Johnson-Nyquist Noise)

Every resistor generates voltage noise:
```
V_noise(rms) = √(4 * k * T * R * BW)
```

Where k = 1.38e-23 J/K, T = temperature in Kelvin (room temp ≈ 300K), R = resistance, BW = bandwidth.

**Rule of thumb at room temperature:**
```
V_noise ≈ 0.13 * √(R * BW) nV
```

A 10kΩ resistor in 10kHz bandwidth: V_noise ≈ 0.13 * √(10e3 * 10e3) ≈ 1.3μV

**Design implication:** Use the lowest resistance values that your circuit can tolerate. High-impedance circuits are inherently noisier.

### Shot Noise

Current through a junction (diode, transistor base-emitter) generates shot noise:
```
I_noise(rms) = √(2 * q * I_DC * BW)
```

Where q = 1.6e-19 C. Shot noise increases with DC current, but the signal-to-noise ratio actually improves at higher currents (signal grows faster than noise).

### 1/f Noise (Flicker Noise)

Noise power increases as frequency decreases. Dominant below a "corner frequency" (1–100Hz for BJTs, 10–10kHz for MOSFETs, varies by op-amp).

**Design implication:** For DC or low-frequency precision, 1/f noise sets the floor. Chopper-stabilized or auto-zero op-amps eliminate 1/f noise by modulating the signal to a higher frequency internally.

### Interference (Not Intrinsic Noise)

External noise sources coupled into your circuit:
- **Capacitive coupling:** Electric fields from nearby conductors (power lines, digital signals, switching nodes)
- **Inductive coupling:** Magnetic fields from current loops (transformers, motors, switching regulators)
- **Conducted noise:** Noise on the power supply rails
- **Ground loops:** Different ground potentials in different parts of the system

## Grounding for Low Noise

### Star Ground Topology

All ground returns converge at a single point near the power supply. This prevents current from one subsystem from flowing through another's ground path.

```
                    ┌── Digital section ── Star point ─┐
Power supply GND ───┤── Analog section ── Star point ──┤── Single point
                    └── Power section ── Star point ──┘
```

### Ground Plane

For PCB design, a continuous ground plane (entire copper layer dedicated to ground) is superior to traces for most designs above a few kHz:
- Low impedance at all frequencies
- Provides shielding
- Return currents naturally flow under the signal trace (path of least inductance)

**Critical rule:** Never cut the ground plane under a sensitive signal path. Slots or cuts force return current to detour, creating a loop antenna.

### Separating Analog and Digital Grounds

- Use separate ground regions that connect at one point (the power supply)
- Route digital signals over the digital ground area, analog signals over the analog ground area
- ADC/DAC chips often have separate AGND and DGND pins — connect them at the chip, not elsewhere
- If using a ground plane, partition it with a narrow bridge at the connection point

## Decoupling and Bypassing

### Why Every IC Needs Bypass Caps

When a digital gate switches, it draws a brief spike of current from V_supply. If this current must travel a long way from the power supply, the inductance of the trace causes a voltage dip (V = L * dI/dt). This dip can:
- Cause other ICs to malfunction
- Radiate EMI
- Couple into analog circuits

A local bypass capacitor acts as a tiny reservoir, supplying the transient current locally.

### Bypass Capacitor Selection

| Frequency Range | Capacitor Type | Value |
|-----------------|----------------|-------|
| DC–1kHz | Electrolytic/Tantalum | 10–100μF |
| 1kHz–10MHz | Ceramic X7R | 100nF–1μF |
| 10MHz–1GHz | Ceramic C0G/NP0 | 1nF–100nF |
| >100MHz | Smallest possible ceramic | 10pF–100pF |

**Standard recipe per IC:**
- 100nF ceramic (X7R) — handles the 1MHz–100MHz range where most switching noise lives
- Add 10μF if the IC draws >100mA or has significant transient demands
- For very high speed (>100MHz), add a second small-value cap (1–10nF)

### Bypass Cap Placement

The cap must be placed between the V+ and GND pins of the IC with the shortest possible trace length. Every mm of trace adds ~1nH of inductance, which reduces the cap's effectiveness at high frequencies.

**Ideal:** Cap directly under the IC (on the opposite side of the PCB) with vias to both power pins.

## Shielding

### When to Shield
- Sensitive high-impedance inputs (photodiode amplifiers, electrometers)
- Very low-level signals (<100μV)
- Circuits near strong EMI sources (motors, switching power supplies, radio transmitters)

### How to Shield
- **Copper pour** connected to ground around sensitive traces on a PCB
- **Metal enclosure** connected to circuit ground at one point
- **Guard ring** around high-impedance nodes — a driven copper ring at the same potential as the sensitive node, intercepting leakage currents

### Guard Ring for High-Impedance Circuits

When measuring pA-level currents, surface leakage across the PCB can exceed the signal. A guard ring at the same potential as the sensitive node intercepts this leakage:

```
    Guard (driven to same voltage as sense node)
    ┌──────────────────┐
    │  ┌────────────┐  │
    │  │ Sense node  │  │
    │  └────────────┘  │
    └──────────────────┘
```

The op-amp's output (or a buffer) drives the guard ring, so there's no voltage difference to drive leakage current into the sense node.

## Layout Rules for Precision Circuits

1. **Keep analog and digital sections separate** on the PCB
2. **Route sensitive signals away from switching nodes** (especially the SW node of switching regulators)
3. **Use differential signaling** for signals that must travel long distances
4. **Minimize loop areas** — signal and return should be adjacent (or use a ground plane)
5. **No signal traces under inductors** (switching regulator inductors radiate)
6. **Keep high-impedance nodes short** — they're antennas for pickup
7. **Thermal symmetry** — if temperature gradients affect precision, make the layout thermally symmetric around the critical components

## Precision Voltage References

For ADCs, DACs, and precision measurement, you need a stable voltage reference — not a power supply rail.

### Common Reference Types

| Type | Example | Accuracy | Tempco | Notes |
|------|---------|----------|--------|-------|
| Bandgap | LM4040, REF3033 | 0.1–1% | 10–100ppm/°C | Most common, moderate precision |
| Buried Zener | LTZ1000, REF102 | 0.01% | 0.05–2ppm/°C | Highest precision, expensive |
| XFET | ADR4540, ADR441 | 0.02% | 2ppm/°C | Good precision, lower noise |

### Reference Usage Rules
1. **Decouple the reference output** with a low-ESR capacitor (check datasheet for stability requirements)
2. **Don't load the reference directly** if possible — buffer it with a precision op-amp
3. **The reference is only as good as its power supply** — feed it from a clean, stable supply
4. **Allow warm-up time** for high-precision references (the LTZ1000 takes 30+ minutes to reach spec)

## Measurement Techniques

### Four-Wire (Kelvin) Sensing

For precision resistance measurement or voltage measurement at a remote load, use separate sense wires:
- **Force wires** carry the current
- **Sense wires** measure the voltage (connected at the point of interest)

Since the sense wires carry negligible current, the voltage drop in the force wires doesn't affect the measurement.

### Ratiometric Measurement

Instead of measuring absolute voltage, measure a ratio. If both the reference and the signal experience the same drift (same supply, same temperature), the ratio stays constant. Most ADCs work this way — the reading is V_in / V_ref, so reference drift cancels if V_in is derived from the same reference.

### Oversampling and Averaging

For slow-changing signals, take many readings and average:
- **Each 4x oversampling adds 1 bit of effective resolution** (requires uncorrelated noise > 1 LSB)
- 10-bit ADC with 16x oversampling ≈ 12-bit effective resolution
- Works only if there's sufficient noise (dithering) on the input to decorrelate samples

## Thermal Design for Precision

- **Thermocouple effects:** Junctions of dissimilar metals generate voltage (Seebeck effect). A copper-to-solder-to-copper joint generates ~1–3μV/°C. This matters at μV-level precision.
- **Resistor tempco:** Even "precision" resistors drift 5–25ppm/°C. At 20°C change, a 25ppm/°C resistor shifts 0.05%.
- **Op-amp offset drift:** Typically 1–10μV/°C. Chopper amps achieve <0.05μV/°C.
- **Keep thermal gradients small** — use a thermal shield, keep heat sources away from precision circuits, let the system reach thermal equilibrium before measuring.
