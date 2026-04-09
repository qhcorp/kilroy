# Active Filters and Oscillators

## Passive Filters — The Basics

### RC Low-Pass Filter
```
V_in ──[R]──┬── V_out
             │
            [C]
             │
            GND
```

```
f_cutoff = 1 / (2π * R * C)
```

Above f_cutoff, attenuation increases at **-20dB/decade** (first-order). At f_cutoff, output is -3dB (≈ 0.707 * V_in).

### RC High-Pass Filter
```
V_in ──||──┬── V_out
     C     │
          [R]
           │
          GND
```

Same formula for f_cutoff. Below f_cutoff, attenuation increases at -20dB/decade.

### Key Insight: Impedance vs Frequency

A capacitor's impedance decreases with frequency: `Z_C = 1 / (2π * f * C)`
An inductor's impedance increases with frequency: `Z_L = 2π * f * L`

Filters are just frequency-dependent voltage dividers. At the cutoff frequency, the reactive impedance equals the resistive impedance.

## Active Filters

Active filters use op-amps to provide gain, sharp cutoffs, and buffered outputs without inductors.

### Why Active Filters?
- **Sharper cutoffs** than passive filters (higher-order responses without loss)
- **No inductors** — inductors are large, expensive, and lossy at low frequencies
- **Buffered output** — the filter's characteristics don't change with load
- **Gain** — can amplify while filtering

### Filter Response Types

| Type | Characteristic | Use When |
|------|---------------|----------|
| Butterworth | Maximally flat passband, -3dB at cutoff | Default choice — flattest passband |
| Chebyshev | Steeper rolloff, ripple in passband | Need steep cutoff, can tolerate ripple |
| Bessel | Maximally flat group delay (no overshoot) | Pulse/square wave signals, time-domain |

### Sallen-Key Low-Pass Filter (2nd Order)

The most common active filter topology:

```
V_in ──[R1]──┬──[R2]──┬── (+)
              │         │     Op-Amp ── V_out
             [C1]      [C2]    (-)────┘
              │         │
             GND       GND
```

For a Butterworth response with equal resistors (R1 = R2 = R):
```
f_cutoff = 1 / (2π * R * √(C1 * C2))
C1 / C2 ≈ 2 (for Butterworth Q = 0.707)
```

**Practical design procedure:**
1. Choose f_cutoff
2. Pick R (1kΩ–100kΩ range)
3. Calculate C from f_cutoff = 1/(2π * R * C), then set C1 = 2C, C2 = C
4. Verify with simulation

### Sallen-Key High-Pass Filter (2nd Order)

Swap Rs and Cs:
```
V_in ──||──┬──||──┬── (+)
     C1    │  C2  │     Op-Amp ── V_out
          [R1]   [R2]    (-)────┘
           │      │
          GND    GND
```

### Multiple Feedback (MFB) Band-Pass Filter

For narrow bandpass filtering:
```
V_in ──[R1]──┬──[C1]── V_out
              │
             [R2]──┬
              │    │
             [C2] [R3]
              │    │
             GND  (-)
                Op-Amp
                  (+)
                   │
                  GND
```

The MFB topology gives better high-frequency rejection than Sallen-Key.

### Higher-Order Filters

To get steeper rolloff, cascade 2nd-order sections:
- **4th order** (-80dB/decade): Two 2nd-order stages
- **6th order** (-120dB/decade): Three 2nd-order stages

Each stage has a different Q value. Use Butterworth polynomial tables to find the Q for each stage:
- 4th order Butterworth: Q1 = 0.541, Q2 = 1.307
- 6th order Butterworth: Q1 = 0.518, Q2 = 0.707, Q3 = 1.932

Higher-Q stages are more sensitive to component tolerances. Use 1% resistors and C0G/NP0 capacitors for precision.

## Oscillators

### What Makes an Oscillator

An oscillator is an amplifier with positive feedback that satisfies the **Barkhausen criterion**:
1. Loop gain ≥ 1 at the oscillation frequency
2. Total phase shift around the loop = 0° (or 360°)

### 555 Timer — The Universal Timer/Oscillator IC

The 555 is the most commonly used timer IC. It contains two comparators, an SR flip-flop, a discharge transistor, and a resistor voltage divider that sets thresholds at 1/3 and 2/3 of V_CC.

#### 555 Internal Structure
- **Threshold comparator:** Trips when pin 6 (THRESH) > 2/3 V_CC → resets flip-flop → output LOW
- **Trigger comparator:** Trips when pin 2 (TRIG) < 1/3 V_CC → sets flip-flop → output HIGH
- **Discharge transistor:** Pin 7 (DISCH) is an open-collector NPN that is ON when output is LOW
- **Reset:** Pin 4 (RESET), active LOW, overrides everything
- **Control voltage:** Pin 5 (CTRL) provides access to the 2/3 V_CC reference. Bypass with 10nF to ground.

#### 555 Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | GND | Ground |
| 2 | TRIG | Trigger input (< 1/3 Vcc sets output HIGH) |
| 3 | OUT | Output |
| 4 | RESET | Active-low reset (tie to Vcc if unused) |
| 5 | CTRL | Control voltage (bypass with 10nF to GND) |
| 6 | THRESH | Threshold input (> 2/3 Vcc resets output LOW) |
| 7 | DISCH | Discharge (open collector, ON when output LOW) |
| 8 | VCC | Supply voltage (4.5V–16V) |

#### 555 Astable Mode (Free-Running Oscillator)

```
VCC ──[R1]──┬──[R2]──┬── DISCH (pin 7)
            │         │
            │        THRESH (pin 6)
            │         │
            │        TRIG (pin 2)
            │         │
            │        [C] ── GND
            │
           OUT (pin 3)
```

The capacitor charges through R1 + R2 and discharges through R2 only.

```
f = 1.44 / ((R1 + 2*R2) * C)
Duty cycle = (R1 + R2) / (R1 + 2*R2)
t_high = 0.693 * (R1 + R2) * C
t_low = 0.693 * R2 * C
```

**Note:** The basic astable circuit always has duty cycle > 50%. For 50% duty cycle:
- Add a diode across R2 (cathode toward pin 7) so charge path is R1 only and discharge path is R2 only
- Or use the output to toggle a flip-flop (divides frequency by 2 but gives exact 50%)

**Component selection guidelines:**
- R1, R2: 1kΩ to 10MΩ. Below 1kΩ, the 555 can't source enough current. Above 10MΩ, leakage currents affect timing.
- C: 100pF to 1000μF. For precision timing, use film or C0G/NP0 ceramic. Avoid electrolytics for timing (poor tolerance and leakage).
- For 1Hz: R1 = 10kΩ, R2 = 680kΩ, C = 1μF → f ≈ 1.05Hz

#### 555 Monostable Mode (One-Shot)

```
VCC ──[R]──┬── DISCH (pin 7)
           │
          THRESH (pin 6)
           │
          [C] ── GND

TRIG (pin 2) ── trigger input (falling edge)
```

A negative pulse on TRIG starts the cycle. Output goes HIGH for:
```
t_pulse = 1.1 * R * C
```

Then output returns LOW and the circuit waits for the next trigger.

### CMOS 555 Variants

The original NE555 has drawbacks: high supply current (~10mA), output glitches during transitions, limited to ~500kHz. **CMOS versions (LMC555, TLC555, ICM7555) fix these:**
- Supply current: 100–250μA (vs 10mA)
- Output swings rail-to-rail
- Works down to 2V supply
- Cleaner output transitions

**Use CMOS 555 for battery-powered designs or when driving CMOS logic.**

### RC Oscillators (Op-Amp Based)

#### Wien Bridge Oscillator
```
         [R]──||── (+)
          │    C    │
          │         │
V_out ────┤      Op-Amp ── V_out
          │         │
          │   (-)──┤
          │        [R_f]
         [R]──||──┤
          │    C  [R1]
         GND      │
                 GND
```

```
f = 1 / (2π * R * C)
Gain must be exactly 3 (R_f / R1 = 2)
```

Gain of exactly 3 is hard to maintain — use an amplitude-limiting mechanism (lamp, FET, or AGC) to stabilize amplitude.

#### Relaxation Oscillator (Schmitt Trigger)
An op-amp with positive feedback (Schmitt trigger) and an RC timing network:

```
       [C]
GND──||──┬── (-)
         │       Op-Amp ── V_out ──┬
         │   (+)──┬                │
         │        [R2]             │
         │        │               [R_f]
         │       [R1]              │
         │        │                │
         │       GND              (+) input
         │                         │
         └─────────────────────────┘
```

This produces a square wave. Frequency depends on R, C, and the feedback ratio.

### Crystal Oscillators

For precision frequency generation (>0.01% accuracy), use a quartz crystal. Crystals are not designed from scratch — you buy them at standard frequencies (32.768kHz, 1MHz, 4MHz, etc.) and use them in a standard oscillator circuit.

**For microcontroller clocks:** Use the crystal oscillator circuit recommended in the microcontroller datasheet. Don't improvise — the load capacitor values matter.

## Waveform Generation Summary

| Waveform | Simplest Method | Precision Method |
|----------|----------------|------------------|
| Square wave | 555 astable or Schmitt trigger oscillator | Crystal oscillator |
| Triangle wave | Integrator driven by square wave | ICL8038 or XR2206 |
| Sine wave | Wien bridge oscillator | DDS (direct digital synthesis) IC |
| Pulse (one-shot) | 555 monostable | Retriggerable monostable (74HC123) |
| PWM | 555 with modulated control voltage | Microcontroller timer peripheral |
| Sawtooth | Constant current into capacitor + reset | DDS IC |

## SPICE Simulation Notes for Oscillators

- **Oscillators need a kick to start.** In SPICE, add a small initial condition on the timing capacitor (e.g., `.ic V(timing_node)=0.1`) or a startup pulse.
- **Transient analysis must run long enough** to see steady-state oscillation. For a 1Hz oscillator, run at least 5 seconds.
- **Timestep matters.** For a 1kHz oscillator, use a maximum timestep of 10μs or smaller to capture waveform shape.
- **555 timer behavioral models** often use B-sources with cross-coupled comparators. See the circuit-design pipeline for a working approach.
