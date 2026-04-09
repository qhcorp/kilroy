# Design Procedures

Step-by-step methodologies for common circuit design tasks.

## General Circuit Design Process

1. **Define requirements.** What must the circuit do? What are the constraints (voltage, current, size, cost, temperature)?
2. **Choose a topology.** Select the circuit architecture that meets the requirements with the least complexity. Don't over-engineer.
3. **Select components.** Start with active components (ICs, transistors), then design the passive network around them. Use standard parts.
4. **Calculate values.** Apply the relevant equations. Use standard component values (E12/E24 series).
5. **Check corner cases.** What happens at minimum/maximum supply voltage? At temperature extremes? With worst-case component tolerances? At startup? At shutdown?
6. **Simulate.** Verify the design in SPICE before building.
7. **Prototype and test.** Measure the actual circuit and compare to simulation.

## Procedure: LED Indicator Circuit

**Given:** Supply voltage (V_S), LED color, desired brightness

1. Look up LED V_f for the chosen color (red ≈ 2V, green ≈ 2.1V, blue/white ≈ 3.2V)
2. Choose LED current: 5–10mA for indicator, 20mA for maximum brightness
3. Calculate: `R = (V_S - V_f) / I_LED`
4. Select nearest standard resistor value (E12 series)
5. Verify: `P_R = (V_S - V_f)^2 / R` — must be within resistor rating
6. If driven by a logic output, verify the pin can source/sink the required current

**Example:** 12V automotive, red LED, 10mA
- R = (12 - 2.0) / 0.010 = 1000Ω → 1kΩ (E12 standard)
- P_R = 100 / 1000 = 100mW → 1/4W resistor is fine

## Procedure: Transistor Switch

**Given:** Load (type, voltage, current), control signal (voltage, source impedance)

1. **Determine switch type:**
   - Load to ground: N-channel MOSFET (preferred) or NPN BJT
   - Load to V+: P-channel MOSFET or PNP BJT
   - Inductive load: MOSFET preferred (built-in body diode helps, but still add external flyback diode)

2. **For MOSFET:**
   a. Select device: V_DS > V_supply * 1.5, I_D > I_load * 2
   b. Verify V_GS from your control signal fully enhances the MOSFET (check R_DS(on) at your V_GS)
   c. For 3.3V control: must use logic-level MOSFET (R_DS(on) specified at V_GS = 2.5V or 3.3V)
   d. Add gate pulldown resistor (10kΩ–100kΩ) for defined OFF state at startup
   e. Add gate series resistor (10–100Ω) for EMI reduction
   f. For inductive loads: verify flyback diode is present

3. **For BJT:**
   a. Select device: V_CE > V_supply * 1.5, I_C > I_load * 2
   b. Calculate I_B: `I_B = I_load / β_min * overdrive` (overdrive = 3–10)
   c. Calculate R_base: `R_B = (V_control - 0.7) / I_B`
   d. Add base-emitter pulldown (10kΩ–47kΩ) for defined OFF state
   e. For inductive loads: add flyback diode across the load

4. **Verify power dissipation:**
   - MOSFET: `P = I_load^2 * R_DS(on)` — usually negligible
   - BJT: `P = V_CE(sat) * I_load` — usually small but check

## Procedure: Op-Amp Amplifier

**Given:** Input signal range, required gain, frequency range, source impedance, load impedance

1. **Determine configuration:**
   - Need high input impedance? → Non-inverting
   - Need virtual ground summing? → Inverting
   - Need gain of 1 (buffer)? → Voltage follower
   - Need to amplify a difference? → Differential or instrumentation amp

2. **Calculate resistor values:**
   - Inverting: `R_f = |Gain| * R_in` (choose R_in = 1kΩ–100kΩ)
   - Non-inverting: `R_f = (Gain - 1) * R_1` (choose R_1 = 1kΩ–100kΩ)

3. **Select op-amp:**
   - GBW must be > Gain * max_frequency (ideally 10x for flat response)
   - Slew rate must be > 2π * f * V_peak (to avoid distortion)
   - Input bias current * source impedance must be << signal level
   - If single-supply: choose rail-to-rail I/O op-amp
   - If high-impedance source: choose FET-input op-amp

4. **Add DC biasing (single-supply):**
   - Bias non-inverting input to V_supply/2
   - AC-couple input and output if needed

5. **Check stability:**
   - Capacitive load? Add series output resistor (10–100Ω)
   - Gain close to unity with decompensated amp? Use a compensated type
   - Add feedback capacitor (1–10pF across R_f) if needed

6. **Add bypass capacitors:** 100nF on each supply pin, close to the IC

## Procedure: Voltage Regulator Selection

**Given:** Input voltage range, output voltage, output current, noise sensitivity

```
Calculate: P_dissipated = (V_in_max - V_out) * I_out
```

### Decision Tree

1. **P_dissipated < 0.5W?** → Linear regulator (LDO)
   - Simple, low noise, no external inductor needed
   - Choose LDO with dropout < (V_in_min - V_out)
   - Verify thermal capability in your package

2. **P_dissipated 0.5–2W?** → Linear with heatsink, or switching
   - If noise-sensitive (analog): linear with adequate heatsink
   - Otherwise: switching regulator

3. **P_dissipated > 2W?** → Switching regulator
   - Buck (step-down): V_out < V_in
   - Boost (step-up): V_out > V_in
   - Buck-boost: V_out can be above or below V_in

4. **Need ultra-low noise for analog?** → Switching regulator followed by LDO
   - Switching handles the large voltage drop efficiently
   - LDO provides the last few hundred mV of drop with clean output

### After selecting the regulator:
- Add input capacitor (per datasheet, minimum 10μF for switching, 1μF for LDO)
- Add output capacitor (per datasheet — check ESR requirements for LDO stability)
- For switching: select inductor (per datasheet), add input/output caps rated for ripple current
- Verify startup behavior (soft-start, inrush current)
- Verify behavior during input transients

## Procedure: 555 Timer Astable (Square Wave Generator)

**Given:** Desired frequency (f) and duty cycle (D)

**For D > 50% (standard circuit):**
1. Choose C (100pF–100μF, avoid electrolytics for timing)
2. Calculate: `R2 = 1 / (1.44 * f * C * (2 - 2*D + D))` — actually, simpler:
   
   ```
   R1 + 2*R2 = 1.44 / (f * C)
   R1 + R2 = (R1 + 2*R2) * D
   ```
   
   Solving:
   ```
   R2 = 1.44 / (f * C) * (1 - D)
   R1 = 1.44 / (f * C) * (2*D - 1)
   ```
   
3. Verify R1 and R2 are in the 1kΩ–10MΩ range
4. Select nearest standard values
5. Recalculate actual f and D with chosen values
6. Add 10nF bypass cap on pin 5 (CTRL)
7. Tie pin 4 (RESET) to VCC

**For 50% duty cycle:**
- Use the diode trick: add a diode across R2 (cathode to pin 7) so charge path bypasses R2
- This gives: f ≈ 1.44 / (2 * R1 * C), duty ≈ 50%
- Or: use 555 to drive a flip-flop (74HC74), dividing frequency by 2 for exact 50%

**For D < 50%:**
- Standard 555 astable cannot achieve D < 50% without modifications
- Use the diode method with R1 < R2
- Or use a CMOS 555 variant with different topology

## Procedure: Power-On Reset

**Given:** Supply voltage, IC reset requirements (active-low/high, minimum pulse width)

### Option 1: RC Reset (Simple, Low-Cost)
1. Determine reset polarity (most ICs use active-low reset)
2. For active-low: R from VCC to RESET, C from RESET to GND
3. Calculate RC time constant: `τ = R * C`
4. Reset deasserts at ~0.63 * VCC (after one time constant)
5. Choose τ = 10 * minimum reset pulse width (for margin)
6. Add Schmitt trigger buffer (74HC14) for clean edges
7. Add a diode across R (cathode to VCC) for fast discharge on power-down (ensures clean reset on rapid power cycling)

### Option 2: Voltage Supervisor (Recommended)
1. Select supervisor IC with threshold just below operating voltage (e.g., 3.08V threshold for 3.3V supply)
2. Connect per datasheet (usually just VCC, GND, and RESET — no external components needed)
3. Verify reset pulse width meets IC requirements
4. Check if the supervisor also monitors brownout (voltage dip detection)

## Procedure: Analog Signal Conditioning

**Given:** Sensor output characteristics, ADC input requirements

1. **Determine signal range:** V_min to V_max from the sensor
2. **Determine ADC input range:** Usually 0–V_ref or -V_ref to +V_ref
3. **Calculate required gain:** `Gain = ADC_range / Sensor_range`
4. **Calculate required offset:** If sensor signal is centered at a non-zero value, you need to subtract the offset or shift the signal
5. **Design the amplifier** (see Op-Amp Amplifier procedure)
6. **Add anti-aliasing filter:** Low-pass filter with cutoff at f_sample/2 or below
   - Use 2nd-order Sallen-Key for most applications
   - Cutoff frequency = Nyquist frequency / 2 to / 5 (depends on filter order and required attenuation)
7. **Add input protection:** Series resistor (1kΩ) + clamp diodes to supply rails
8. **Buffer the signal** at the ADC input if the amplifier output impedance is too high for the ADC's sample-and-hold circuit
