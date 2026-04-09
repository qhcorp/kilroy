# Voltage Regulation and Power Supply Design

## Why Regulate?

Raw power sources (batteries, wall adapters, automotive 12V) are noisy, variable, and often the wrong voltage. Circuits need clean, stable supply rails.

| Source | Typical Range | Noise/Ripple |
|--------|---------------|-------------|
| 9V battery | 9.6V (fresh) to 6V (dead) | Low, but varies with load |
| USB | 4.75V–5.25V (spec), but can sag | Moderate switching noise |
| Automotive "12V" | 9V (cranking) to 14.5V (charging), spikes to 40V+ | Very noisy |
| Wall adapter (unregulated) | Rated voltage ± 20%, varies with load | High ripple |
| Wall adapter (regulated/switching) | ±5% of rated | Switching noise at 50–500kHz |

## Linear Regulators

### How They Work

A linear regulator is essentially a variable resistor (pass transistor) controlled by a feedback loop. It drops the excess voltage as heat.

```
P_dissipated = (V_in - V_out) * I_load
```

**This is the fundamental trade-off:** Simple, low noise, but wastes power as heat.

### Three-Terminal Fixed Regulators (78xx / LM1117)

The simplest solution. Three pins: IN, OUT, GND.

**78xx series (positive):**
| Part | V_out | I_max | Dropout |
|------|-------|-------|---------|
| 7805 | 5.0V | 1.0A | ~2V |
| 7812 | 12.0V | 1.0A | ~2V |
| 7833 | 3.3V | 1.0A | ~2V |

**LDO (Low-Dropout) regulators:**
| Part | V_out | I_max | Dropout |
|------|-------|-------|---------|
| LM1117-3.3 | 3.3V | 800mA | 1.2V |
| AMS1117-3.3 | 3.3V | 1A | 1.3V |
| MCP1700-33 | 3.3V | 250mA | 178mV |
| AP2112K-3.3 | 3.3V | 600mA | 250mV |

### Linear Regulator Design Rules

1. **Input voltage must exceed output by at least the dropout voltage.** For a 7805, V_in must be at least 7V. For an LDO with 200mV dropout, V_in must be at least V_out + 0.2V.

2. **Input capacitor:** 0.33μF minimum (ceramic) close to the input pin. Required for stability. Some regulators oscillate without it.

3. **Output capacitor:** 0.1μF minimum (ceramic) close to the output pin. Some LDOs require specific ESR range for stability — check the datasheet. Tantalum capacitors with ESR of 0.1–1Ω are often specified.

4. **Thermal design:** Calculate P = (V_in - V_out) * I_load. For a TO-220 package without a heatsink, thermal resistance is ~60°C/W. At 2W dissipation, the junction temperature rises 120°C above ambient — that's too hot.

5. **Heatsink rule of thumb:** If P_dissipated > 1W, you probably need a heatsink or a switching regulator.

### When NOT to Use a Linear Regulator

- V_in >> V_out (e.g., 12V to 3.3V at 500mA → 4.35W wasted as heat)
- High current (>1A in most cases)
- Battery-powered designs where efficiency matters
- When the heat can't be managed

In these cases, use a switching regulator.

### Adjustable Linear Regulators (LM317)

The LM317 uses two resistors to set the output voltage:

```
V_in ── [LM317 IN] ── [OUT] ──┬── V_out
                    [ADJ]──┐   │
                           [R2] [R1]
                           │    │
                          GND  │
                               └── ADJ
```

Wait — correct topology:
```
V_out = 1.25 * (1 + R2/R1)
```

Where R1 connects from OUT to ADJ (typically 240Ω) and R2 connects from ADJ to GND.

## Switching Regulators

### How They Work

Switching regulators rapidly switch a transistor on and off, storing energy in an inductor (or capacitor) and delivering it to the output at a different voltage. Efficiency is typically 80–95%.

### Switching Regulator Topologies

| Topology | Function | V_out Range | Complexity |
|----------|----------|-------------|------------|
| Buck | Step-down | V_out < V_in | Low |
| Boost | Step-up | V_out > V_in | Low |
| Buck-Boost | Step-up or step-down | Any | Medium |
| Inverting (Cuk) | Negative voltage from positive | V_out < 0 | Medium |
| SEPIC | Step-up or step-down, non-inverting | Any positive | Medium |
| Flyback | Isolated, any ratio | Any (isolated) | High |

### Buck Converter Design (Step-Down)

The most common switching regulator. Converts a higher voltage to a lower voltage efficiently.

**Key components:**
1. **Switching element** (internal or external MOSFET)
2. **Inductor** — stores energy during the ON phase, delivers it during OFF
3. **Output capacitor** — smooths the output voltage
4. **Diode or synchronous MOSFET** — provides current path when switch is OFF
5. **Feedback network** — resistor divider that sets the output voltage

**Design parameters:**
```
Duty cycle: D = V_out / V_in
Inductor ripple current: ΔI_L = (V_in - V_out) * D / (f_sw * L)
Output voltage ripple: ΔV_out ≈ ΔI_L / (8 * f_sw * C_out)
```

**Component selection rules:**
- **Inductor:** Choose L so that ΔI_L is 20–40% of I_load. Larger L = less ripple but slower transient response.
- **Output capacitor:** Choose C_out for acceptable ripple voltage. Use low-ESR ceramics.
- **Input capacitor:** Must handle the RMS ripple current. Use ceramics rated for the current.
- **Diode:** Use Schottky for efficiency (low V_f). Or use synchronous rectification (second MOSFET) for even better efficiency.

### Using Switching Regulator Modules/ICs

For most designs, **use an integrated switching regulator IC** rather than building from discrete components. The IC includes the control loop, oscillator, and often the switching MOSFET.

**Popular buck regulator ICs:**
| Part | V_in Range | V_out | I_out | f_sw | Notes |
|------|-----------|-------|-------|------|-------|
| LM2596 | 4.5–40V | Adj | 3A | 150kHz | Easy to use, large components |
| MP1584 | 4.5–28V | Adj | 3A | 1.5MHz | Compact, fewer external parts |
| TPS54331 | 3.5–28V | Adj | 3A | 570kHz | Good efficiency |
| LM3671 | 2.7–5.5V | Adj | 600mA | 2MHz | Tiny, for battery devices |

**Popular boost regulator ICs:**
| Part | V_in Range | V_out | I_out | Notes |
|------|-----------|-------|-------|-------|
| MT3608 | 2–24V | Up to 28V | 2A switch | Common in modules |
| TPS61023 | 0.5–5.5V | Adj | 500mA | Low-voltage start |

### Switching Regulator Layout Rules

Layout is critical for switching regulators. Poor layout causes noise, instability, and EMI.

1. **Keep the switching loop small.** The path from V_in through the switch, inductor, output cap, and back through the input cap should be as short as possible.
2. **Ground plane** under the switching regulator. No high-impedance traces crossing under the inductor.
3. **Input and output capacitors** as close to the IC as physically possible.
4. **Feedback resistors** close to the IC, away from the switching node.
5. **The switching node (SW)** is the noisiest point. Keep it small and away from sensitive signals.

## Power Supply Filtering

### Capacitor Filtering Stages

For clean power to sensitive circuits, use multiple filtering stages:

```
V_raw ──[C_bulk]──[Ferrite bead]──[C_ceramic]── V_clean
                                      │
                                     [C_small]
                                      │
                                     GND
```

- **C_bulk** (10–100μF electrolytic): Handles large, slow current demands
- **Ferrite bead** (600Ω @ 100MHz): Blocks high-frequency noise
- **C_ceramic** (1–10μF X7R): Filters mid-frequency noise
- **C_small** (100nF ceramic): Filters high-frequency noise

### Power Supply Decoupling Per IC

Every IC needs local decoupling:
```
V_supply rail ──┬── IC V+ pin
                │
              [100nF]
                │
               GND ──── IC GND pin
```

For analog ICs, add a 10μF in parallel. For very high-speed digital, add 10nF in parallel.

## Protection Circuits

### Reverse Polarity Protection

**Series diode:** Simple, but drops 0.3–0.7V.
```
V_in ──|>|── V_protected
```

**P-MOSFET:** Near-zero voltage drop, better for high-current.
```
V_in ── Source──[PMOS]──Drain ── V_protected
               Gate ── V_in (through resistor, clamped with Zener)
```

### Overvoltage Protection

**TVS diode:** Clamps voltage spikes. Place across the input, cathode to V+.
```
V_in ──┬── Circuit
       │
     [TVS]
       │
      GND
```

### Overcurrent Protection

**Fuse:** Simplest. Choose rating at 1.5–2x normal operating current.

**Polyfuse (PTC):** Resettable. Resistance increases dramatically when current exceeds the trip point. Slower than a regular fuse.

**Current-limiting circuit:** Active circuit using a sense resistor and transistor.

## Automotive Power Design

Automotive 12V is one of the harshest power environments:
- Normal: 13.5V (engine running)
- Cranking: Can drop to 6V
- Load dump: Spikes to 40V+ (up to 100V for short duration)
- Reverse battery: -12V if connected backwards
- EMI: Ignition noise, alternator whine

**Design approach:**
1. TVS diode (bidirectional, 24V) on the input
2. Reverse polarity protection (P-MOSFET or series diode)
3. LC filter for EMI
4. Wide-input buck regulator (e.g., LM2596, rated to 40V input)
5. Secondary LDO for clean analog supply if needed

## Battery Power Design

### Battery Characteristics

| Type | V_nominal | V_full | V_empty | Notes |
|------|-----------|--------|---------|-------|
| Alkaline (AA) | 1.5V | 1.6V | 0.9V | Non-rechargeable |
| NiMH (AA) | 1.2V | 1.4V | 1.0V | Rechargeable, flat discharge |
| Li-Ion (18650) | 3.7V | 4.2V | 3.0V | High energy, needs protection |
| LiPo | 3.7V | 4.2V | 3.0V | Same chemistry, pouch form |
| Li-Ion (2S) | 7.4V | 8.4V | 6.0V | Two cells in series |
| 9V (alkaline) | 9V | 9.6V | 6.0V | Low capacity (~500mAh) |

### Battery Design Rules
1. **Never connect Li-Ion cells without a protection circuit** (BMS) — they can catch fire if overcharged, over-discharged, or short-circuited
2. **Design for the full voltage range** — a "3.7V" Li-Ion varies from 3.0V to 4.2V
3. **Minimize quiescent current** — every μA counts. Use low-Iq regulators, sleep modes, and power switches.
4. **LDO vs. buck:** An LDO from 4.2V to 3.3V wastes 21% of the energy. A buck converter wastes 5–10%. For battery life, this matters.
