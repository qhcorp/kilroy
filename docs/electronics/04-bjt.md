# Bipolar Junction Transistors (BJTs)

## How BJTs Work — The Essential Mental Model

A BJT is a current-controlled device. A small current into the base controls a much larger current through the collector.

**The key relationship:** `I_C = β * I_B` (or equivalently, `I_C ≈ I_E` since I_B is small)

Where β (hFE) is the current gain, typically 100–300 for small-signal transistors. **Never design a circuit that depends on a specific β value** — it varies wildly between individual transistors, with temperature, and with current.

### NPN vs PNP

- **NPN:** Current flows from collector to emitter. Base must be ~0.6V above emitter to turn on. The workhorse — use NPN by default.
- **PNP:** Current flows from emitter to collector. Base must be ~0.6V below emitter to turn on. Used for high-side switching and complementary circuits.

### The Transistor as Two Diodes (Approximate)

Think of a transistor as two back-to-back diodes:
- **Base-Emitter junction:** Forward-biased in active mode. V_BE ≈ 0.6V (silicon).
- **Base-Collector junction:** Reverse-biased in active mode. Forward-biased in saturation.

This model is approximate but catches most design errors.

## BJT Operating Regions

| Region | B-E Junction | B-C Junction | Use |
|--------|-------------|-------------|-----|
| Cutoff | Reverse | Reverse | Switch OFF |
| Active | Forward | Reverse | Amplifier |
| Saturation | Forward | Forward | Switch ON |

## BJT as a Switch

This is the most common use of BJTs in digital and mixed-signal circuits.

### Design Procedure for NPN Switch

Given: V_supply, load current I_load, logic signal V_logic

1. **Choose the transistor.** I_C(max) must exceed I_load with margin. V_CE(max) must exceed V_supply.

2. **Calculate base current for saturation:**
   ```
   I_B = I_load / β_min * overdrive_factor
   ```
   Use β_min from the datasheet (not typical), and overdrive_factor of 3–10x to guarantee hard saturation.

3. **Calculate base resistor:**
   ```
   R_base = (V_logic - V_BE) / I_B
   ```
   Where V_BE ≈ 0.7V in saturation.

4. **Verify saturation voltage:** In saturation, V_CE(sat) is typically 0.1–0.3V. The load sees V_supply - V_CE(sat).

5. **Add a base-emitter resistor (optional but recommended):** A 10kΩ–47kΩ resistor from base to emitter prevents noise from turning on the transistor when the drive signal is floating or high-impedance.

### Example: Switching a Relay

12V relay coil draws 50mA. Driven from a 3.3V logic output.

```
Choose: 2N2222 (I_C max = 800mA, V_CE max = 40V, β_min ≈ 75)
I_B = 50mA / 75 * 5 = 3.3mA (5x overdrive)
R_base = (3.3 - 0.7) / 3.3mA = 788Ω → use 680Ω
Add flyback diode across relay coil (mandatory for inductive loads)
Add 10kΩ base-emitter pulldown
```

### Common Switch Mistakes
- **No flyback diode on inductive loads** — will destroy the transistor
- **Relying on typical β** — use β_min and add overdrive
- **Forgetting V_CE(sat)** — the switch doesn't go to 0V; it's 0.1–0.3V
- **No base pulldown** — floating base = unpredictable behavior

## BJT as an Amplifier

### The Three Amplifier Configurations

| Configuration | Input | Output | Voltage Gain | Current Gain | Input Z | Output Z | Use |
|--------------|-------|--------|-------------|-------------|---------|----------|-----|
| Common Emitter | Base | Collector | High (inverts) | High | Medium | Medium-High | General voltage amplification |
| Common Collector (Emitter Follower) | Base | Emitter | ~1 (no inversion) | High | High | Low | Buffer, impedance transformation |
| Common Base | Emitter | Collector | High (no inversion) | ~1 | Low | High | High-frequency amplifiers, cascode |

### Common Emitter Amplifier — The Workhorse

**Biasing procedure (voltage divider bias):**

1. Set V_C at roughly V_supply/2 for maximum signal swing
2. Set V_E at 1–2V (allows emitter resistor for stability)
3. V_B = V_E + 0.6V
4. Choose I_C (typically 0.1–10mA for small-signal)
5. R_C = (V_supply - V_C) / I_C
6. R_E = V_E / I_C
7. Voltage divider: I_divider ≈ 10 * I_B. Then:
   ```
   R2 = V_B / I_divider
   R1 = (V_supply - V_B) / I_divider
   ```

**Voltage gain:**
- Without bypass capacitor: `A_v = -R_C / R_E` (stable, predictable)
- With bypass capacitor on R_E: `A_v = -R_C / r_e` where `r_e ≈ 26mV / I_C` (high gain, less stable)

**Rule of thumb:** Gain without bypass cap is limited to ~100–200. For higher gain, use multiple stages or an op-amp.

### Emitter Follower (Common Collector)

The emitter follower has no voltage gain but has:
- **High input impedance:** Z_in ≈ β * (R_E || R_load)
- **Low output impedance:** Z_out ≈ R_source / β + r_e
- **Near-unity voltage gain:** V_out = V_in - 0.6V

**Use it to:** Drive low-impedance loads from high-impedance sources. Buffer a sensor output before sending it down a cable. Drive a capacitive load.

## Current Mirrors

A current mirror copies a reference current to one or more outputs.

### Basic NPN Current Mirror
```
V+ ──[ R_ref ]──┬──── V+ ──[Load]──┐
                 │                   │
                Q1(C,B)            Q2(C)
                 │                   │
                Q1(E)              Q2(E)
                 │                   │
                GND                GND
```

Q1 is diode-connected (collector tied to base). The V_BE of Q1 sets the V_BE of Q2, so Q2's collector current matches Q1's collector current.

```
I_ref = (V+ - V_BE) / R_ref
I_out ≈ I_ref (for matched transistors)
```

### Current Mirror Accuracy
- Transistors must be **matched** (same type, same temperature). In ICs, they're on the same die. For discrete, use matched pairs or a transistor array.
- **Early effect** causes I_out to vary with V_CE(Q2). Wilson or cascode mirrors improve this.
- **β error:** Each transistor's base current steals from the reference. Error ≈ 2/β. Use high-β transistors or a Wilson mirror.

## Darlington Pair

Two transistors cascaded so the emitter of Q1 drives the base of Q2. Total β = β1 * β2 (thousands).

**Trade-offs:**
- V_BE(total) ≈ 1.2V (two junctions in series)
- V_CE(sat) ≈ 0.7–1.0V (worse than single transistor)
- Slower switching (Miller capacitance)

**Use when:** You need very high current gain (driving a big load from a tiny signal) and don't care about saturation voltage.

## Common BJT Models for SPICE

### Small-Signal NPN (2N2222 / 2N3904)
```
.model Q2N2222 NPN (IS=14.34f BF=255 VAF=74.03 BR=6.092 RC=1 RB=10)
.model Q2N3904 NPN (IS=6.734f BF=416.4 VAF=74.03 BR=0.7389 RC=1 RB=10)
```

### Small-Signal PNP (2N2907 / 2N3906)
```
.model Q2N2907 PNP (IS=650.6e-18 BF=231.7 VAF=116.1 BR=3.563 RC=0.715 RB=10)
.model Q2N3906 PNP (IS=1.41f BF=180 VAF=115 BR=4 RC=2.5 RB=10)
```

### Key SPICE Model Parameters

| Parameter | Meaning | Typical Range |
|-----------|---------|---------------|
| IS | Transport saturation current | 1e-16 to 1e-12 |
| BF | Forward current gain (β) | 100–400 |
| BR | Reverse current gain | 0.1–10 |
| VAF | Forward Early voltage | 50–200V |
| RB | Base resistance | 1–100Ω |
| RC | Collector resistance | 0.1–10Ω |
| RE | Emitter resistance | 0.01–1Ω |
| CJC | B-C junction capacitance | 1–20pF |
| CJE | B-E junction capacitance | 5–50pF |
| TF | Forward transit time | 0.1–1ns |
