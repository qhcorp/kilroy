# Operational Amplifiers

## The Two Golden Rules

When an op-amp is operating in its linear region (with negative feedback):

1. **The output does whatever is necessary to make the voltage difference between the inputs zero.** (V+ ≈ V-)
2. **The inputs draw no current.** (I+ = I- = 0)

These rules are approximations (real op-amps have finite gain, finite input impedance, and input bias currents), but they are sufficient for designing 95% of op-amp circuits. **Start every op-amp analysis by applying these two rules.**

### When the Rules Don't Apply
- **No negative feedback** (comparator mode) — the output saturates to one rail or the other
- **Output is saturated** (hitting the supply rails) — the inputs are no longer equal
- **Very high frequency** — gain drops, phase shifts accumulate, feedback may become positive

## Fundamental Op-Amp Circuits

### Inverting Amplifier
```
        R_f
V_in ──[R_in]──┬──[R_f]── V_out
               │
              (-)
           Op-Amp
              (+)
               │
              GND
```

```
V_out = -V_in * (R_f / R_in)
Gain = -R_f / R_in
Input impedance = R_in
```

**Design notes:**
- The inverting input is a "virtual ground" — it sits at 0V (by Golden Rule 1)
- Input impedance is just R_in (the source sees R_in to virtual ground)
- For gain of -10: R_in = 10kΩ, R_f = 100kΩ

### Non-Inverting Amplifier
```
V_in ── (+)
      Op-Amp ── V_out
        (-) ──┬──[R_f]── V_out
              │
             [R1]
              │
             GND
```

```
V_out = V_in * (1 + R_f / R1)
Gain = 1 + R_f / R1
Input impedance = very high (op-amp input impedance)
```

**Design notes:**
- Minimum gain is 1 (when R_f = 0 or R1 = ∞) — the voltage follower
- Input impedance is the op-amp's own input impedance (typically >1MΩ, often >1GΩ for FET-input)
- For gain of 11: R1 = 10kΩ, R_f = 100kΩ

### Voltage Follower (Unity-Gain Buffer)
```
V_in ── (+)
      Op-Amp ── V_out
        (-) ────┘
```

Gain = 1. The most useful circuit in analog electronics. Use it to:
- Buffer a high-impedance source before driving a low-impedance load
- Isolate a sensitive circuit from loading effects
- Drive long cables or capacitive loads

**Caution:** Not all op-amps are stable at unity gain. Check the datasheet for "unity-gain stable" or minimum stable gain.

### Differential Amplifier
```
V1 ──[R1]──┬──[R2]── V_out
            (-)
         Op-Amp
            (+)
V2 ──[R3]──┤
            [R4]
            │
           GND
```

When R1 = R3 and R2 = R4:
```
V_out = (V2 - V1) * (R2 / R1)
```

**Design notes:**
- Resistor matching is critical — 1% mismatch in a gain-of-1 diff amp gives ~60dB CMRR, not the 100dB+ you'd expect
- For high CMRR, use an instrumentation amplifier IC instead of discrete resistors
- Good for measuring voltage across a current-sense resistor

### Summing Amplifier
```
V1 ──[R1]──┐
V2 ──[R2]──┤──[R_f]── V_out
V3 ──[R3]──┘
            (-)
         Op-Amp
            (+)
            │
           GND
```

```
V_out = -R_f * (V1/R1 + V2/R2 + V3/R3)
```

If all input resistors are equal: `V_out = -(R_f/R) * (V1 + V2 + V3)`

### Integrator
```
          C_f
V_in ──[R]──┬──||── V_out
            (-)
         Op-Amp
            (+)
            │
           GND
```

```
V_out = -(1 / RC) * ∫V_in dt
```

**Practical requirement:** Add a large resistor (1MΩ–10MΩ) in parallel with C_f to prevent DC drift from saturating the output. This limits the low-frequency integration to f > 1/(2π * R_f * C_f).

### Differentiator
```
           R_f
V_in ──||──┬──[R_f]── V_out
          (-)
       Op-Amp
          (+)
          │
         GND
```

```
V_out = -R_f * C * dV_in/dt
```

**Warning:** Pure differentiators amplify high-frequency noise. Always add a small resistor in series with C (forming a low-pass filter) to limit the high-frequency gain. Without this, the circuit will oscillate.

## Op-Amp as Comparator

Without negative feedback, an op-amp operates as a comparator:
- V+ > V-: output goes to positive rail
- V+ < V-: output goes to negative rail

### Comparator with Hysteresis (Schmitt Trigger)
Add positive feedback to prevent oscillation at the switching point:

```
V_in ── (-)
      Op-Amp ── V_out
        (+) ──┬──[R2]── V_out
              │
             [R1]
              │
            V_ref
```

```
Hysteresis = (V_high - V_low) * R1 / (R1 + R2)
Upper threshold = V_ref + hysteresis/2
Lower threshold = V_ref - hysteresis/2
```

**Note:** For actual comparator applications, use a comparator IC (LM311, LM393), not an op-amp. Comparators have faster response, open-collector/open-drain outputs, and are designed for rail-to-rail output swings. Op-amps used as comparators can have slow recovery from saturation and may latch up.

## Practical Op-Amp Selection

### Key Specifications

| Spec | What It Means | When It Matters |
|------|--------------|-----------------|
| GBW (Gain-Bandwidth Product) | Gain * frequency = constant | High-frequency signals |
| Slew Rate | Max output voltage change rate (V/μs) | Large, fast signals |
| Input Offset Voltage (V_os) | Voltage difference between inputs when output is zero | DC precision |
| Input Bias Current (I_b) | Current flowing into/out of inputs | High-impedance sources |
| Input Offset Current (I_os) | Difference between the two bias currents | Precision with matched source impedances |
| CMRR | Common-mode rejection ratio | Differential measurements |
| PSRR | Power supply rejection ratio | Noisy supply environments |
| Rail-to-Rail I/O | Can output/input swing to supply rails | Single-supply, low-voltage |

### Op-Amp Selection Guidelines

| Application | Key Specs | Example Parts |
|-------------|-----------|---------------|
| General purpose | GBW > 1MHz, moderate precision | LM358, TL072, NE5532 |
| Precision DC | V_os < 100μV, low drift | OPA277, AD8628, LTC1050 |
| High speed | GBW > 100MHz, high slew rate | AD8065, OPA657, LTC6268 |
| Single supply, rail-to-rail | RRIO, low voltage | MCP6001, LMV321, OPA340 |
| High impedance source | FET input, I_b < 1pA | OPA129, AD549, LMP7721 |
| Audio | Low noise, low distortion | NE5532, OPA2134, OPA1612 |

### Single-Supply Operation

Many circuits assume dual supplies (±15V, ±12V, ±5V). For single-supply operation:

1. **Create a virtual ground** at V_supply/2 using a voltage divider buffered by an op-amp
2. **AC-couple** inputs and outputs with capacitors
3. **Bias the non-inverting input** to V_supply/2
4. **Use rail-to-rail op-amps** — standard op-amps can't swing closer than ~1.5V to either rail
5. **The output cannot go below ground** — signals are limited to 0V to V_supply

### Stability

Op-amp circuits can oscillate if phase shift in the feedback loop reaches 180° at a frequency where the loop gain is still >1.

**Stability checklist:**
- Capacitive loads (>100pF) can cause oscillation. Add a small series resistor (10–100Ω) between the output and the capacitive load.
- Long feedback paths add stray capacitance. Keep feedback resistors close to the op-amp.
- Compensation capacitor across R_f (small value, 1–10pF) can stabilize a circuit at the expense of bandwidth.
- Check the datasheet for minimum stable gain — some op-amps (decompensated types) require a minimum gain (e.g., 5 or 10) to be stable.

## Common Op-Amp SPICE Models

For simulation, many op-amp models are complex subcircuits. For basic behavioral simulation:

```
* Simple op-amp macromodel (single-supply, rail-to-rail output)
.subckt OPAMP_SIMPLE inp inn vcc vee out
E1 out 0 VALUE={LIMIT(1e5*V(inp,inn), V(vee)+0.01, V(vcc)-0.01)}
.ends
```

For more accurate simulation, use manufacturer-provided SPICE models (available on the IC manufacturer's website).

### Behavioral Op-Amp with Bandwidth Limiting
```
.subckt OPAMP_BW inp inn vcc vee out
E1 mid 0 VALUE={LIMIT(1e5*V(inp,inn), V(vee)+0.01, V(vcc)-0.01)}
R1 mid out 1k
C1 out 0 159p  ; Sets GBW to ~1MHz (1/(2*pi*1k*159p))
.ends
```
