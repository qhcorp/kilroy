# Field-Effect Transistors (FETs)

## FET vs BJT — When to Use Which

| Criterion | BJT | MOSFET |
|-----------|-----|--------|
| Drive | Current-controlled (needs continuous I_B) | Voltage-controlled (gate draws no DC current) |
| Input impedance | Medium (~kΩ) | Extremely high (~10^12 Ω) |
| Switching speed | Fast | Faster (but gate capacitance must be charged) |
| Saturation voltage | V_CE(sat) ≈ 0.1–0.3V | R_DS(on) * I_D (can be very low) |
| Cost | Cheaper for small-signal | Cheaper for power switching |
| Best for | Small-signal amplifiers, current mirrors | Power switching, logic, analog switches |

**Default choice for switching: MOSFET.** Default choice for small-signal analog: BJT (or op-amp).

## MOSFET Fundamentals

### Enhancement Mode (the common type)

- **N-channel:** OFF with V_GS = 0. Turns ON when V_GS > V_th. Current flows from drain to source. Used for low-side switching.
- **P-channel:** OFF with V_GS = 0. Turns ON when V_GS < -|V_th|. Current flows from source to drain. Used for high-side switching.

### Key Parameters

| Parameter | Meaning | Design Impact |
|-----------|---------|---------------|
| V_th (V_GS(th)) | Gate threshold voltage | Minimum voltage to begin turning on. NOT the voltage for full enhancement. |
| R_DS(on) | Drain-source on-resistance | Determines power loss when fully on: P = I_D^2 * R_DS(on) |
| V_DS(max) | Maximum drain-source voltage | Must exceed supply voltage with margin |
| I_D(max) | Maximum continuous drain current | Must exceed load current with margin |
| Q_g | Total gate charge | Determines switching speed and gate drive power |
| V_GS(max) | Maximum gate-source voltage | Typically ±20V. Exceeding this destroys the MOSFET instantly. |

### Critical: V_th vs Full Enhancement

The datasheet V_GS(th) is the voltage where the MOSFET barely starts conducting (typically at 250μA). **Full enhancement requires V_GS well above V_th** — the R_DS(on) spec is given at a specific V_GS (typically 4.5V or 10V).

**Rule:** For a logic-level MOSFET (V_th ≈ 1–2V), drive the gate with at least 4.5V for full enhancement. For a standard MOSFET (V_th ≈ 2–4V), drive the gate with at least 10V.

If you're switching from a 3.3V logic signal, you MUST use a logic-level MOSFET (specified for R_DS(on) at V_GS = 2.5V or 3.3V).

## MOSFET as a Switch

### Low-Side N-Channel Switch (Most Common)

```
V+ ──[Load]──┬── Drain
              │
            MOSFET
              │
             Source ── GND
              │
Gate ──[R_g]──┘
```

- Gate pulled HIGH → MOSFET ON → load energized
- Gate pulled LOW → MOSFET OFF → load de-energized
- **R_g (gate resistor):** 10–100Ω limits peak gate current and reduces ringing. Not always needed but good practice.
- **Gate pulldown:** 10kΩ–100kΩ from gate to source ensures the MOSFET stays OFF when the drive signal is floating (critical during power-up when microcontrollers haven't initialized yet).

### High-Side P-Channel Switch

```
V+ ──┬── Source
     │
   MOSFET
     │
    Drain ──[Load]── GND
     │
Gate ── drive circuit
```

- Gate pulled to V+ (V_GS = 0) → MOSFET OFF
- Gate pulled to GND (V_GS = -V+) → MOSFET ON
- Works well for V+ ≤ 12V where V_GS(max) isn't exceeded
- For V+ > 12V, need a gate driver or level shifter

### High-Side N-Channel Switch

Requires a gate voltage *above* the supply rail (V_GS must be above V_source, which is at V+). This requires a charge pump or bootstrap circuit. Use a gate driver IC for this. Don't try to build it discretely unless you understand the bootstrap timing.

## MOSFET Gate Protection

**The gate oxide is fragile.** It can be destroyed by static electricity (ESD) or voltage spikes.

1. **Never let the gate float** — always provide a defined path to ground or a supply rail
2. **Clamp V_GS** with a Zener diode (12–15V) from gate to source for power MOSFETs in noisy environments
3. **Gate resistor** (10–100Ω) limits current spikes and damps oscillation
4. **Handle MOSFETs with ESD precautions** in the real world

## MOSFET Switching Speed and Gate Drive

MOSFETs switch fast, but the gate capacitance must be charged and discharged. The switching time is determined by:

```
t_switch ≈ Q_g / I_gate
```

For a MOSFET with Q_g = 20nC driven by a gate driver that can source 1A: t_switch ≈ 20ns.

For slow switching (e.g., turning a relay on/off), a microcontroller pin through a resistor is fine. For fast switching (e.g., PWM at >10kHz), use a dedicated gate driver IC.

### Switching Losses

During the transition between OFF and ON (and vice versa), the MOSFET passes through the linear region where both V_DS and I_D are nonzero. Power dissipation during transition:

```
P_switching = 0.5 * V_DS * I_D * (t_rise + t_fall) * f_switching
```

At high frequencies, switching losses dominate over conduction losses.

## JFETs

JFETs are depletion-mode devices — they're ON with V_GS = 0 and turn OFF as V_GS goes negative (N-channel) or positive (P-channel).

### JFET Applications
- **Constant-current sources:** A JFET with gate tied to source passes I_DSS (the zero-bias drain current). Simple, no additional components.
- **Analog switches:** Low distortion, bidirectional
- **High-impedance amplifier inputs:** Very low gate leakage current (pA)
- **Voltage-controlled resistors:** In the triode region, a JFET acts as a voltage-controlled resistor

### JFET Constant Current Source
```
V+ ──[Load]── Drain
               │
             JFET (gate tied to source)
               │
              Source ── GND
```

Current = I_DSS (from datasheet, typically 1–10mA). To set a lower current, add a source resistor:
```
I_D ≈ I_DSS * (1 - V_GS/V_P)^2
R_S = |V_GS| / I_D
```

## MOSFET Body Diode

Every MOSFET has an intrinsic body diode from source to drain (N-channel) or drain to source (P-channel). This means:
- An N-channel MOSFET cannot block current from source to drain
- The body diode is slow (high reverse recovery time) — it can cause problems in switching converters
- In synchronous rectifier applications, the body diode conducts during dead time

## Common MOSFET Selections

### Logic-Level N-Channel (Low-Side Switching)
| Part | V_DS | I_D | R_DS(on) @ V_GS | Notes |
|------|------|-----|------------------|-------|
| 2N7000 | 60V | 200mA | 5Ω @ 4.5V | TO-92, small loads only |
| IRLZ44N | 55V | 47A | 22mΩ @ 4V | Logic-level, high current |
| IRF3205 | 55V | 110A | 8mΩ @ 10V | NOT logic-level (needs 10V gate) |

### P-Channel (High-Side Switching)
| Part | V_DS | I_D | R_DS(on) @ V_GS | Notes |
|------|------|-----|------------------|-------|
| NDP6020P | -20V | -24A | 50mΩ @ -4.5V | Logic-level P-channel |
| IRF9540 | -100V | -23A | 117mΩ @ -10V | Standard (needs -10V gate drive) |

## SPICE Modeling Notes

### Simple MOSFET Model
```
.model NMOS_SW NMOS (VTO=2 KP=20m RD=0.1 RS=0.1)
.model PMOS_SW PMOS (VTO=-2 KP=10m RD=0.1 RS=0.1)
```

### Key MOSFET SPICE Parameters

| Parameter | Meaning | Typical Range |
|-----------|---------|---------------|
| VTO | Threshold voltage | 1–4V (N-ch), -1 to -4V (P-ch) |
| KP | Transconductance parameter | 10m–200m |
| RD | Drain resistance | 0.01–1Ω |
| RS | Source resistance | 0.01–1Ω |
| CBD | Drain-body capacitance | 10p–1nF |
| CBS | Source-body capacitance | 10p–1nF |
| CGS | Gate-source capacitance | 100p–10nF |
| CGD | Gate-drain capacitance | 10p–1nF |

### JFET SPICE Model
```
.model J_2N5457 NJF (VTO=-1.8 BETA=1.3m LAMBDA=2.25m IS=33.57f)
```
