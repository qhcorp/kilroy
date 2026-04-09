# Digital Logic

## Logic Families

### Key Families and Their Properties

| Family | V_supply | Speed | Power | Output | Notes |
|--------|---------|-------|-------|--------|-------|
| 74HC | 2–6V | 25MHz | Low | Push-pull | Default choice for new designs |
| 74HCT | 5V only | 25MHz | Low | Push-pull | HC with TTL-compatible thresholds |
| 74AC | 2–6V | 125MHz | Medium | Push-pull | Fast, but noisy edges |
| 74LVC | 1.65–3.6V | 150MHz | Low | Push-pull | Low-voltage, 5V tolerant inputs |
| 74AHC | 2–5.5V | 200MHz | Low | Push-pull | Advanced HC, faster |
| CD4000 | 3–15V | 4MHz | Very low | Push-pull | Wide supply range, very slow |
| TTL (74LS) | 5V only | 35MHz | Medium | Totem-pole | Legacy, avoid in new designs |

### Logic Level Definitions

| Family | V_IH (min) | V_IL (max) | V_OH (min) | V_OL (max) |
|--------|-----------|-----------|-----------|-----------|
| 74HC (5V) | 3.5V | 1.5V | 4.9V | 0.1V |
| 74HC (3.3V) | 2.3V | 1.0V | 3.2V | 0.1V |
| TTL/74HCT | 2.0V | 0.8V | 2.7V | 0.4V |
| 74LVC (3.3V) | 2.0V | 0.8V | 3.2V | 0.1V |
| CMOS (generic) | 70% V_DD | 30% V_DD | ~V_DD | ~0V |

**Critical concept:** A valid HIGH must be above V_IH. A valid LOW must be below V_IL. The gap between V_OL and V_IL (or V_OH and V_IH) is the **noise margin** — the amount of noise the signal can tolerate before being misread.

### Interfacing Between Logic Families

#### 3.3V to 5V
- **If 5V input is 5V-tolerant on the 3.3V side:** Just connect (many 74LVC parts are 5V tolerant)
- **If not 5V-tolerant:** Use a level shifter or resistor divider
- **3.3V output driving 5V CMOS input:** May not work — 3.3V might not reach V_IH of 3.5V for HC at 5V. Use 74HCT (TTL thresholds, V_IH = 2.0V) on the 5V side.

#### 5V to 3.3V
- **Resistor divider:** Simple but slow (R + stray capacitance forms a low-pass filter)
- **Series resistor + clamp diode:** Better for faster signals
- **Level shifter IC:** Best for bidirectional or high-speed (BSS138-based, TXB0108, etc.)

#### Open-Drain/Open-Collector Outputs
These can only pull LOW. They need an external **pull-up resistor** to the desired logic level. Advantage: multiple outputs can share a line (wired-OR/wired-AND), and the pull-up can be to any voltage.

```
Pull-up value: R = V_pull / I_sink(max)
Typical: 1kΩ–10kΩ for general logic, 4.7kΩ for I2C
```

## Digital Timing

### Propagation Delay

Every gate has a delay from input change to output change (t_PD, typically 5–20ns for 74HC). In a chain of N gates, total delay = N * t_PD.

### Setup and Hold Times

For flip-flops and registers:
- **Setup time (t_SU):** Data must be stable this long BEFORE the clock edge
- **Hold time (t_H):** Data must remain stable this long AFTER the clock edge

Violating setup/hold times causes **metastability** — the output may settle to an unpredictable state, oscillate, or take an abnormally long time to resolve.

### Clock Distribution

- **Fan-out:** Each gate output can drive a limited number of inputs (typically 10 for HC). Exceeding fan-out degrades signal integrity.
- **Skew:** Different path lengths cause different arrival times. Keep clock paths equal in length for synchronous design.
- **Use a clock buffer** (74HC125, dedicated clock buffer) for distributing a clock to many loads.

## Common Digital Building Blocks

### Flip-Flops

| Type | Behavior | Use |
|------|----------|-----|
| D flip-flop | Output follows D on clock edge | Registers, synchronization, delay |
| JK flip-flop | J=K=1 toggles | Counters, dividers |
| T flip-flop | Toggles on every clock edge | Frequency division |
| SR latch | Set/Reset | Simple state storage (avoid in synchronous design) |

### Counters

- **Binary counter (74HC393):** Counts in binary. Each stage divides frequency by 2.
- **Decade counter (74HC4017):** Counts 0–9, one-hot output. Good for sequencing.
- **Up/down counter (74HC191):** Counts in either direction.

### Shift Registers

- **74HC595:** Serial-in, parallel-out. Use to expand output pins from a microcontroller (SPI-driven).
- **74HC165:** Parallel-in, serial-out. Use to read many inputs with few pins.

### Multiplexers and Decoders

- **74HC151:** 8:1 multiplexer. Selects one of 8 inputs.
- **74HC138:** 3-to-8 decoder. One of 8 outputs goes active based on 3-bit input.
- **74HC4051:** Analog multiplexer. Passes analog signals, not just logic levels.

## Debouncing

Mechanical switches bounce — a single press produces multiple transitions over 1–10ms. Digital circuits see these as multiple events.

### Hardware Debounce

**RC filter + Schmitt trigger:**
```
Switch ──[R]──┬── Schmitt trigger input (74HC14)
              [C]
              GND
```

R = 10kΩ, C = 100nF gives τ = 1ms. The Schmitt trigger's hysteresis cleans up the slow RC edge.

**SR latch debounce (for SPDT switches):**
```
VCC ──[R1]──┬── S (set)     ┌── Q (debounced output)
            NC               │
  Switch ──────            SR Latch
            NO               │
VCC ──[R2]──┬── R (reset)  └── Q_bar
```

This produces a clean, bounce-free transition on the first contact.

### Software Debounce

Read the switch, wait 10–20ms, read again. If both reads agree, accept the value. This is simpler and costs no hardware, but requires a microcontroller.

## Driving Loads from Digital Logic

### LED from Logic Output
```
Output ──[R]──|>|── GND    (active HIGH, sourcing)
VCC ──[R]──|>|── Output   (active LOW, sinking — preferred)
```

Most logic gates can source/sink 4–25mA directly. Check the datasheet.

### Relay or Motor from Logic
Logic outputs cannot drive relays or motors directly. Use a transistor (BJT or MOSFET) as a switch. See [BJT switching](04-bjt.md) and [MOSFET switching](05-fet.md).

### Buzzer/Speaker
Piezo buzzers: Can often be driven directly from a logic output (they draw <20mA).
Magnetic buzzers/speakers: Need a transistor driver and a flyback diode.

## Reset Circuits

Most digital ICs and microcontrollers need a clean reset at power-up.

### Simple RC Reset
```
VCC ──[R]──┬── RESET pin
           [C]
           GND
```

At power-up, C is discharged, holding RESET low. C charges through R, eventually releasing RESET. Time constant = R * C (choose for ~100ms).

**Problem:** Slow power supply ramp-up may not produce a clean reset. The RC voltage may linger in the undefined region.

### Supervisory IC (Preferred)
Use a voltage supervisor (MAX809, TPS3839, etc.) that holds RESET active until V_supply is above a threshold and stable. These also detect brownouts (momentary voltage dips).
